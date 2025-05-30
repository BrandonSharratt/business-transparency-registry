<template>
  <div class="relative w-full">
    <Combobox v-model="val" :nullable="true">
      <div class="mt-1">
        <div
          :class="[
            'w-full',
            'cursor-default',
            'overflow-hidden',
            'bg-gray-100',
            'hover:bg-gray-200',
            'text-left',
            'border-b-[1px]',
            'focus:border-b-2',
            errorState ? 'border-red-500' : 'border-gray-700',
            'focus:outline-none',
            'sm:text-sm',
            'h-[56px]',
            'rounded-t-md'
          ]"
        >
          <ComboboxInput
            :placeholder="$t('labels.line1')"
            :display-value="() => line1"
            class="bg-transparent pl-2 w-full h-full focus:outline-none"
            :class="errorState ? 'placeholder-red-500' : 'placeholder-gray-700'"
            data-cy="address-street"
            @keyup="doTheSearch($event.target.value)"
            @blur="$emit('blur', $event)"
          />
        </div>
        <ComboboxOptions
          :class="[
            'absolute',
            'mt-1',
            'max-h-60',
            'w-full',
            'overflow-auto',
            'bg-white',
            'py-1',
            'text-base',
            'shadow-lg',
            'focus:outline-none',
            'sm:text-sm',
            'z-10']"
          data-cy="address-street-options"
        >
          <ComboboxOption
            v-for="address in suggestedAddresses"
            :key="address.Id"
            v-slot="{ selected, active }"
            as="template"
          >
            <li
              class="cursor-default select-none py-2 pl-10 pr-4"
              :class="{
                'bg-gray-200 text-primary-500': active,
                'text-gray-700': !active,
              }"
              @mousedown="selectFromDropdown(address, $event)"
            >
              <span
                class="block"
                :class="{ 'font-medium': selected, 'font-normal': !selected }"
              >
                {{ address.Text }} &nbsp; {{ address.Description }}
              </span>
            </li>
          </ComboboxOption>
        </ComboboxOptions>
      </div>
    </Combobox>
  </div>
</template>

<script setup lang="ts">
import { ref, type Ref } from 'vue'
import { Combobox, ComboboxInput, ComboboxOption, ComboboxOptions } from '@headlessui/vue'
import type { CanadaPostApiFindResponseItemI, CanadaPostRetrieveItemI } from '~/utils'
import type { BtrAddressI } from '~/interfaces/btr-address-i'

const runtimeConfig = useRuntimeConfig()

// eslint-disable-next-line func-call-spacing
const emit = defineEmits<{
  (e: 'addrAutoCompleted', value: BtrAddressI): void
  (e: 'update:modelValue', value: string): void
  (e: 'blur', value: FocusEvent): void
}>()
const props = defineProps({
  countryIso3166Alpha2: { type: String, required: false, default: 'CA' },
  maxSuggestions: { type: Number, required: false, default: 7 },
  langCode: { type: String, required: false, default: 'ENG' },
  modelValue: { type: String, required: true },
  errorState: { type: Boolean, default: false }
})

const canadaPostApiKey = runtimeConfig.public.addressCompleteKey
const suggestedAddresses: Ref<Array<CanadaPostApiFindResponseItemI>> = ref([])
// @ts-ignore
const line1: Ref<string> = ref('')

watch(
  () => props.modelValue,
  (newValue: string) => {
    line1.value = newValue
  },
  { immediate: true }
)

const val = ref()
val.value = { id: 'empty' }
const selectFromDropdown = async (address: CanadaPostApiFindResponseItemI, event: Event) => {
  if (address?.Next === 'Find') {
    event.stopPropagation()
    event.preventDefault()

    suggestedAddresses.value = await findAddress(line1.value, address.Id, props, canadaPostApiKey)
  } else {
    const address1 = await getExactAddress(address.Id)
    line1.value = address1.Line1
    const btrAddr: BtrAddressI = convertToBtrAddress(address1)
    emit('addrAutoCompleted', btrAddr)
  }
}

const convertToBtrAddress = (addr: CanadaPostRetrieveItemI): BtrAddressI => {
  return {
    country: { alpha_2: addr.CountryIso2, name: addr.CountryName },
    line1: addr.Line1,
    line2: addr.Line2,
    city: addr.City,
    region: addr.Province,
    postalCode: addr.PostalCode,
    locationDescription: ''
  }
}

const doTheSearch = async (searchTerm: string) => {
  // todo: add debounce
  line1.value = searchTerm
  suggestedAddresses.value = await findAddress(searchTerm, '', props, canadaPostApiKey)
}

const getExactAddress = async (searchAddressId: string): Promise<CanadaPostRetrieveItemI> => {
  const retrievedAddresses = await retrieveAddress(searchAddressId, canadaPostApiKey)
  let addrForLang = retrievedAddresses.find(addr => addr.Language === props.langCode)
  if (!addrForLang && retrievedAddresses) {
    addrForLang =
      retrievedAddresses.find(addr => addr.Language === 'ENG') ||
      retrievedAddresses[0]
  }
  return addrForLang as CanadaPostRetrieveItemI
}

watch(line1, (newLine1: string, _: string) => {
  emit('update:modelValue', newLine1)
})

watch(() => props.modelValue, (newValue: string) => {
  line1.value = newValue
})

</script>
