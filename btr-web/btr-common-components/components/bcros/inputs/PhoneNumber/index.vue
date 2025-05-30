<template>
  <div class="flex flex-row gap-4 w-full">
    <UFormGroup :name="name + '.countryCode'" class="w-1/4">
      <BcrosInputsPhoneNumberCountryCode
        v-model:country-calling-code="phoneNumber.countryCallingCode"
        v-model:country-code2letter-iso="phoneNumber.countryCode2letterIso"
        data-cy="phoneNumber.countryCode"
        :placeholder="$t('placeholder.phoneNumber.countryCode')"
        @update:country-code2letter-iso="$emit('country-change')"
      />
    </UFormGroup>
    <UFormGroup :name="name + '.number'" class="w-1/2">
      <template #help="{ error }">
        <span v-if="error">
          {{ error }}
        </span>
        <BcrosTooltip
          v-else
          :popper="{
            placement: 'bottom',
            arrow: true,
            resize: true
          }"
        >
          <template #tooltip-text>
            <span class="whitespace-normal place-content: center">
              {{ $t('helpTexts.phoneNumber.tooltip') }}
            </span>
          </template>
          <span class="text-xs">
            {{ $t('helpTexts.phoneNumber.hint') }}
          </span>
        </BcrosTooltip>
      </template>
      <template #default="{ error }">
        <UInput
          v-model="maskedPhoneNumber"
          v-maska:unmaskedvalue.unmasked
          data-cy="phoneNumber.number"
          :data-maska="inputMask"
          :placeholder="$t('placeholder.phoneNumber.number')"
          :variant="error ? 'error' : 'bcGov'"
          @focus="clearPhoneNumberOnEdit"
          @change="phoneNumberUpdated=true"
          @blur="revertUnchangedPhoneNumber"
        />
      </template>
    </UFormGroup>
    <UFormGroup :name="name + '.extension'" class="w-1/4">
      <UInput
        v-model="phoneNumber.extension"
        :placeholder="$t('placeholder.phoneNumber.extension')"
        variant="bcGov"
        data-cy="phoneNumber.extensionCode"
      />
      <template #help>
        <span class="text-xs">
          {{ $t('general.optional') }}
        </span>
      </template>
    </UFormGroup>
  </div>
</template>

<script setup lang="ts">
import { vMaska } from 'maska/vue'
import { Mask } from 'maska'

import { type PhoneSchemaType } from '~/interfaces/zod-schemas-t'

const emit = defineEmits<{(e: 'country-change'): void }>()

const phoneNumber = defineModel<PhoneSchemaType>({ required: true })

const props = defineProps({
  name: { type: String, default: 'phoneNumber' },
  isEditing: { type: Boolean, required: true }
})

const northAmericaMask = '(###) ###-####'
const otherMask = '##############'

const unmaskedvalue = ref()
const maskedPhoneNumber = ref(phoneNumber.value.number)
const inputMask = computed(() => phoneNumber.value.countryCallingCode === '1' ? northAmericaMask : otherMask)

watchEffect(
  () => {
    const mask = new Mask({ mask: inputMask.value })
    phoneNumber.value.number = unmaskedvalue.value || mask.unmasked(maskedPhoneNumber.value || '')
  }
)

const phoneNumberUpdated = ref(false)
const phoneFieldUuid = getRandomUuid()
const clearPhoneNumberOnEdit = () => {
  if (props.isEditing) {
    setFieldOriginalValue(phoneFieldUuid, maskedPhoneNumber)
    maskedPhoneNumber.value = ''
  }
}
const revertUnchangedPhoneNumber = () => {
  const originalValue = getFieldOriginalValue(phoneFieldUuid)
  if (props.isEditing && !phoneNumberUpdated.value && originalValue) {
    maskedPhoneNumber.value = originalValue
  }
}

onMounted(() => {
  if (phoneNumber.value.countryCallingCode !== undefined) {
    emit('country-change')
  }
})
</script>
