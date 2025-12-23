/**
 * Utility functions for text selection detection
 */

/**
 * Gets the currently selected text on the page
 * @returns The selected text string, or null if no text is selected
 */
export const getSelectedText = (): string | null => {
  const selection = window.getSelection();
  if (selection && selection.toString().trim() !== '') {
    return selection.toString().trim();
  }
  return null;
};

/**
 * Checks if any text is currently selected on the page
 * @returns Boolean indicating if text is selected
 */
export const isTextSelected = (): boolean => {
  return getSelectedText() !== null;
};

/**
 * Gets the DOM range of the current selection (if any)
 * @returns The selection range or null if no selection
 */
export const getSelectedRange = (): Range | null => {
  const selection = window.getSelection();
  if (selection && selection.rangeCount > 0) {
    return selection.getRangeAt(0);
  }
  return null;
};