declare module "@toast-ui/editor" {
  export type EditorOptions = {
    el: HTMLElement;
    height?: string;
    initialValue?: string;
    initialEditType?: "markdown" | "wysiwyg";
    previewStyle?: "tab" | "vertical";
    theme?: "dark" | string;
    language?: string;
    usageStatistics?: boolean;
    autofocus?: boolean;
    hideModeSwitch?: boolean;
    placeholder?: string;
    toolbarItems?: string[][];
  };

  export default class Editor {
    constructor(options: EditorOptions);
    on(eventName: string, handler: (...args: unknown[]) => void): void;
    getMarkdown(): string;
    destroy(): void;
  }
}
