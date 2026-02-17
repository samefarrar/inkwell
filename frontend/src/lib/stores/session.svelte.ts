/**
 * Session state store — tracks current screen, session data, and workflow state.
 * Uses Svelte 5 runes for reactivity.
 */

export type Screen = 'task' | 'interview' | 'drafts' | 'focus';

export interface ThoughtBlock {
  assessment: string;
  missing: string[];
  sufficient: boolean;
}

export interface ChatMessage {
  role: 'user' | 'ai' | 'thought' | 'status';
  content: string;
  thought?: ThoughtBlock;
}

class SessionStore {
  screen = $state<Screen>('task');
  taskType = $state('');
  topic = $state('');
  messages = $state<ChatMessage[]>([]);
  readyToDraft = $state(false);
  draftSummary = $state('');
  keyMaterial = $state<string[]>([]);

  startInterview(taskType: string, topic: string): void {
    this.taskType = taskType;
    this.topic = topic;
    this.messages = [];
    this.readyToDraft = false;
    this.screen = 'interview';
  }

  addMessage(msg: ChatMessage): ChatMessage {
    this.messages = [...this.messages, msg];
    // Return the reactive proxy (last element of the $state array)
    return this.messages[this.messages.length - 1];
  }

  setReadyToDraft(summary: string, keyMaterial: string[]): void {
    this.readyToDraft = true;
    this.draftSummary = summary;
    this.keyMaterial = keyMaterial;
  }

  goToDrafts(): void {
    this.screen = 'drafts';
  }

  goToFocus(): void {
    this.screen = 'focus';
  }

  reset(): void {
    this.screen = 'task';
    this.taskType = '';
    this.topic = '';
    this.messages = [];
    this.readyToDraft = false;
    this.draftSummary = '';
    this.keyMaterial = [];
  }
}

export const session = new SessionStore();
