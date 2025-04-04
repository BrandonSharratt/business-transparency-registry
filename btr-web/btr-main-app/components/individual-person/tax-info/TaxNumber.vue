<template>
  <div class="flex flex-col py-5">
    <div class="flex flex-row mb-2 py-1">
      <UFormGroup
        ref="taxNumberInputGroupRef"
        v-slot="{ error }"
        :name="name+'.taxNumber'"
      >
        <UInput
          v-model="taxNumber"
          data-cy="tax-number-input"
          type="text"
          :variant="error ? 'error' : variant"
          :placeholder="$t('placeholders.taxNumber')"
          class="w-80"
          @focusout="formatInput"
          @change="handleInput"
          @focus="focusTaxNumber"
          @blur="revertUnchangedTaxNumber"
        />
      </UFormGroup>
    </div>

    <UFormGroup v-slot="{ error }" :name="name + '.hasTaxNumber'">
      <div class="flex flex-row items-center mb-2 py-2">
        <UCheckbox
          id="noTaxNumberRadioButton"
          v-model="noTaxNumber"
          data-cy="no-tax-number-checkbox"
          :value="false"
          :variant="error ? 'error' : variant"
          @change="toggleCheckbox"
        />
        <label for="noTaxNumberRadioButton" class="ml-5" :class="{ 'text-red-500': error}">
          {{ $t('labels.noTaxNumberLabel') }}
        </label>
      </div>
    </UFormGroup>
  </div>
</template>

<script setup lang="ts">
const hasTaxNumber = defineModel('hasTaxNumber', { type: Boolean, required: false, default: undefined })
const taxNumber = defineModel('taxNumber', { type: [String, undefined], required: false, default: undefined })

// eslint-disable-next-line func-call-spacing
const emit = defineEmits<{
  (e: 'clear-errors', path: string): void
  (e: 'tax-number-changed', path: string): void
  (e: 'has-tax-number-changed'): void
}>()

const props = defineProps<{ name: string, variant: string, isEditing: boolean }>()

const taxNumberInputGroupRef = ref() // UFormGroup ref
const formatInput = () => {
  taxNumber.value = formatTaxNumber(taxNumber.value)
}

const taxNumberFieldUuid = getRandomUuid()
const taxNumberChanged = ref(false)

const noTaxNumber = ref(hasTaxNumber.value === false)

const focusTaxNumber = () => {
  emit('clear-errors', props.name + '.hasTaxNumber')
  hasTaxNumber.value = true
  noTaxNumber.value = false
  if (props.isEditing) {
    setFieldOriginalValue(taxNumberFieldUuid, taxNumber.value)
    taxNumber.value = ''
  }
}

const revertUnchangedTaxNumber = () => {
  const originalValue = getFieldOriginalValue(taxNumberFieldUuid)
  if (props.isEditing && !taxNumberChanged.value && originalValue) {
    taxNumber.value = originalValue
  }
}

const clearTaxNumber = () => {
  emit('clear-errors', props.name + '.taxNumber')
  taxNumber.value = undefined
}

/**
 * Format the tax number to "xxx xxx xxx"
 * @param {string} taxNumber - string representation of the tax number input
 */
const formatTaxNumber = (taxNumber: string | undefined): string | undefined => {
  if (taxNumber === undefined) {
    return undefined
  }
  // if the tax number cannot pass the above validation checks, it will not be formatted
  if (!checkSpecialCharacters(taxNumber) || !checkTaxNumberLength(taxNumber) || !validateTaxNumber(taxNumber)) {
    return taxNumber
  }

  const digits = taxNumber.replace(/\s+/g, '')

  let formattedNumber: string = ''

  for (let i = 0; i < 9; i++) {
    formattedNumber += digits[i]
    if (i === 2 || i === 5) {
      formattedNumber += ' '
    }
  }

  return formattedNumber
}

const handleInput = () => {
  taxNumberChanged.value = true
  emit('tax-number-changed', taxNumber.value)
}

const toggleCheckbox = () => {
  hasTaxNumber.value = !noTaxNumber.value
  clearTaxNumber()
  emit('has-tax-number-changed')
}
</script>
