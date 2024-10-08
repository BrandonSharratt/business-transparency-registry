<script setup lang="ts">
import { useOmitIndividual } from '@/stores/omit-individual'

const omitIndividual = useOmitIndividual()
const { siBizName } = storeToRefs(omitIndividual)

const ALLOWED_LEGAL_TYPES = [
  'BC',
  'BEN',
  'CBEN',
  'C',
  'CC',
  'CCC',
  'ULC',
  'CUL'
]
const selected = ref({})
const model = defineModel({ type: String, default: '' })
defineProps({
  label: { type: [String], default: '' },
  name: { type: String, default: 'email' },
  placeholder: { type: [String], default: '' },
  id: { type: String, required: true },
  modelValue: { type: String, default: '' },
  variant: { type: String, default: 'bcGov' }
})

const loading = ref(false)
siBizName.value = ''

function updateModel (event) {
  const str: string = '' + event.identifier
  model.value = str
  siBizName.value = event.name
}

async function search (q: string) {
  if (q === '') {
    return []
  }

  loading.value = true

  const runtimeConfig = useRuntimeConfig()
  const url = runtimeConfig.public.searchApiURL + '/search/businesses'
  const key = runtimeConfig.public.searchApiKey
  const searchParams = {
    query: {
      value: q
    },
    categories: {
      legalType: ALLOWED_LEGAL_TYPES
    }
  }
  const { data, error } = await useFetchBcros<any>(url,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-apikey': key },
      body: searchParams
    }
  )
  loading.value = false
  if (error && error.value) {
    return []
  }

  return data.value.searchResults.results
}
</script>

<template>
  <UFormGroup v-slot="{ error }" :label="label" :name="name">
    <USelectMenu
      :id="name"
      v-model="selected"
      :searchable="search"
      :loading="loading"
      variant="outline"
      :placeholder="placeholder"
      option-attribute="name"
      color="gray"
      :class="{ 'text-red-500': !!error}"
      trailing
      by="identifier"
      @change="updateModel($event)"
    >
      <template #label>
        <span class="truncate">
          {{ selected && selected.identifier && selected.name
            ? `${selected.identifier} - ${selected.name}`
            : placeholder }}
        </span>
      </template>
    </USelectMenu>
  </UFormGroup>
</template>
