/**
 * Type to represent and store highlights within a text
 * @param id ID of highlight span element
 * @param textStartPos Represents start index of highlight on source text
 * @param textEndPos Represents end index of highlight on source text
 * @param text Highlighted text
 * @param caption Caption associated with given text
 * @param htmlStartPos Represents start index of html before inserting this span
 * @param htmlEndPos Represents end index of html before inserting this span
 */
export type HighlightObject = {
    id: string;
    textStartPos: number;
    textEndPos: number;
    text: string;
    caption: string;
    htmlStartPos: number;
    htmlEndPos: number;
}