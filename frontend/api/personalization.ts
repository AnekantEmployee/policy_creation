import apiClient from './client';

export interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ExtractedInfo {
  key: string;
  value: string;
  confidence: number;
}

export interface PersonalizationChatRequest {
  session_id: number;
  user_message: string;
  frameworks: string[];
  policy_types: string[];
  procedure_types: string[];
  conversation_history?: ConversationMessage[];
  extracted_info?: Record<string, string>;
  org_context?: Record<string, any>;
}

export interface PersonalizationChatResponse {
  extracted_info: ExtractedInfo[];
  accumulated_info: Record<string, string>;
  suggestions: string[];
  missing_info: Array<{
    key: string;
    description: string;
    prompt: string;
    priority: string;
  }>;
  assistant_message: string;
  conversation_history: ConversationMessage[];
  is_complete: boolean;
}

export interface GenerateQuestionsRequest {
  org_name: string;
  org_description: string;
  org_country?: string;
  frameworks: string[];
  policy_types: string[];
  procedure_types: string[];
}

export interface GenerateQuestionsResponse {
  questions: Array<{
    key: string;
    label: string;
    hint: string;
    type: 'text' | 'email' | 'phone' | 'textarea' | 'select';
    category: 'contacts' | 'tools' | 'roles' | 'processes' | 'legal' | 'technical';
    options?: string[];
  }>;
  source: 'ai' | 'static';
}

export const personalizationApi = {
  /**
   * Generate AI-tailored (or static fallback) personalization questions.
   */
  async generateQuestions(request: GenerateQuestionsRequest): Promise<GenerateQuestionsResponse> {
    const response = await apiClient.post<GenerateQuestionsResponse>(
      '/personalization/generate-questions',
      request
    );
    return response.data;
  },

  /**
   * Send a conversational message for personalization.
   * System extracts info, identifies gaps, and provides suggestions.
   */
  async chat(request: PersonalizationChatRequest): Promise<PersonalizationChatResponse> {
    const response = await apiClient.post<PersonalizationChatResponse>(
      '/personalization/chat',
      request
    );
    return response.data;
  },

  /**
   * Get framework-specific suggestions.
   * Optional query parameter to filter suggestions.
   */
  async getSuggestions(framework: string, query?: string): Promise<{
    framework: string;
    suggestions: string[];
  }> {
    const response = await apiClient.get(
      `/personalization/suggestions/${framework}`,
      { params: { query } }
    );
    return response.data;
  },
};
