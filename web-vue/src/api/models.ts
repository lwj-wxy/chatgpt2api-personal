import apiClient from './client'

export interface ImageModelProfile {
  model: string
  label: string
  selection_mode: 'compatibility_alias' | 'conversation_tool' | 'tool_model'
  upstream_model: string
  image_model_verified: boolean
  size_mode: 'prompt_hint' | 'native_parameter'
  quality_mode: 'prompt_hint' | 'native_parameter'
  size_label: string
  quality_label: string
  note: string
  size_options: { value: string; label: string; ratio: string; resolution: 'auto' | '1K' | '2K' | '4K' }[]
  quality_options: { value: string; label: string }[]
}

export interface ModelCatalogResponse {
  object: 'model_catalog'
  schema_version: 1
  generated_at: string
  revision: string
  chat_models: string[]
  image_models: string[]
  all_models: string[]
  image_profiles?: ImageModelProfile[]
  defaults: {
    chat_model: string
    image_model: string
  }
  capabilities: {
    image_upscale: boolean
    high_resolution_image_models: string[]
  }
  source: {
    chat: 'config' | 'accounts' | 'fallback'
    image: 'config' | 'accounts' | 'fallback'
  }
  openai_models_endpoint: '/v1/models'
}

export const modelsApi = {
  catalog: () => apiClient.get<never, ModelCatalogResponse>('/api/model-catalog'),
}
