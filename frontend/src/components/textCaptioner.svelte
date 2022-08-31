<script lang="ts">
    import { onMount, createEventDispatcher } from 'svelte';
    import type { HighlightObject } from '../highlight';

    export let text = "";
    export let busy = false;
    
    var dispatch = createEventDispatcher();

    /**
     * Creates and styles span element used for highlighting text within paragraph
     * @param id ID of span element
     */
    function createHighlightSpan(id: string): HTMLSpanElement{
        let span = document.createElement('span');
        span.classList.add("text-xl");
        span.classList.add("font-bold");
        span.id = id;
        return span;
    }

    /**
     * Show (or hide) caption upon hovering (or lifting) on a highlighted span
     * @param this Highlighted text element
     * @param event Event causing the update
     */
    function spanHover(this:HTMLSpanElement, event:MouseEvent){
        let id = this.id.split("span ")[1];
        let caption = <HTMLElement> document.getElementById("caption " + id);
        caption.hidden = !caption.hidden;
    }

    /**
     * Returns a stylized caption element to be embed over highlighted span
     */
    function createCaption():HTMLSpanElement{
        let captionElement = document.createElement("span");
        /* TODO: Replace with tailwind if needed */
        captionElement.style.padding = "0.1em 0.5em 0.1em 0.5em";
        captionElement.style.zIndex = "999";
        captionElement.style.backgroundColor = "white";
        captionElement.style.border = "4px dotted black";

        return captionElement;
    }

    /**
     * Appends caption to a specified highlight span
     * @param highlight Highlight object
     */
    function addCaption(highlight: HighlightObject): void{
        const caption = highlight.caption;
        const id = highlight.id;
        let captionElement = createCaption();
        captionElement.id = "caption " + id.split("span ")[1];
        captionElement.innerText = caption;
        let spanElement = <HTMLElement> document.getElementById(id);
        spanElement?.after(captionElement);
        let captionrect = captionElement.getBoundingClientRect();
        let spanrect = spanElement.getBoundingClientRect();
        captionElement.hidden = true;
        captionElement.style.position = "absolute";
        captionElement.style.left = "" + (spanrect.left + spanrect.width/2 - captionrect.width/2) + "px";
        captionElement.style.top = "" + (spanrect.top - captionrect.height) + "px";
    }

    /**
     * Highlights selected text by embedding it inside a span
     * @param highlight Highlight object containing highlight data
     */
    function addHighlight(highlight: HighlightObject): void{
        const id = highlight.id;
        const startHtmlPos = highlight.htmlStartPos;
        const endHtmlPos = highlight.htmlEndPos;
        const highlightarea:HTMLElement = <HTMLElement> document.getElementById("highlightarea");
        const prevHtml = highlightarea.innerHTML;
        let highlightSpan = createHighlightSpan(id);
        highlightSpan.innerHTML = prevHtml.substring(startHtmlPos,endHtmlPos);
        highlightarea.innerHTML = prevHtml.substring(0,startHtmlPos) + 
            highlightSpan.outerHTML +
            prevHtml.substring(endHtmlPos);   
    }
    /**
     * Inner function utilized to determine the position of highlighted text
     * 
     * Iteratively checks sibling nodes until we reach start of paragraph node and 
     * adds-up their offsets.
     * 
     * Returns textoffset, htmloffset and number of spans between node and start of paragraph
     * @param node Html Node to calculate offset from
     */
    function getOffset(node: Node|null):number[]{
        let sibling = node?.previousSibling;
        let textOffset = 0;
        let htmlOffset = 0;
        let numSpans = 0;
        
        while(sibling){
            if(sibling.nodeType == Node.ELEMENT_NODE){
                if(sibling.nodeName == "SPAN"){
                    let currentElement = <HTMLElement> sibling.firstChild!.parentElement;
                    
                    if(currentElement.id.startsWith("caption")){
                        /* Caption Node, skip it */
                        htmlOffset += currentElement.outerHTML.length;
                    }
                    else{
                        let elementoffset = currentElement.outerHTML.length;
                        let inneroffset = currentElement.innerHTML.length;
                        textOffset += inneroffset;
                        htmlOffset += elementoffset - inneroffset;
                        numSpans++;
                    }
                }
                else if(sibling.textContent == ""){ 
                    /* For BR element */
                    htmlOffset += 3;
                    textOffset += 1;
                }
                else{
                    /* probably unrelated node, skip it */
                    let elementoffset = sibling.firstChild!.parentElement!.outerHTML.length;
                    htmlOffset += elementoffset;
                }
            }
            else if(sibling.nodeType == Node.TEXT_NODE){
                textOffset += sibling.textContent!.length;
            }
            sibling = sibling.previousSibling;
        }
        return [textOffset,htmlOffset,numSpans];
    }

    /**
     * Called on selecting a given text. Highlights that particular part and
     * adds & stores respective caption
     */
    function onTextSelect(){
        const selection = window.getSelection();

        /* Validate selection to be within text */
        if(!selection || selection.toString() == "")return;
        

        let id = selection.anchorNode?.parentElement?.id;
        if(id != "highlightarea")return;
        if(id != selection.focusNode?.parentElement?.id)return;

        let [anchorTextOffset, anchorHtmlOffset, anchorNumSpans] = getOffset(selection.anchorNode);
        let [focusTextOffset, focusHtmlOffset, focusNumSpans] = getOffset(selection.focusNode);
        if(focusNumSpans != anchorNumSpans)return; // Overlapping hignlightreq

        /* TODO: pls don't do this in final version */
        const caption = window.prompt("Add your caption");
        if(!caption || caption == "")return;
        
        anchorTextOffset += selection.anchorOffset;
        focusTextOffset += selection.focusOffset;
        
        let startTextOffset:number, endTextOffset:number, startHtmlOffset:number, endHtmlOffset:number;
        if((anchorTextOffset + anchorHtmlOffset) > (focusTextOffset + focusHtmlOffset)){
            startTextOffset = focusTextOffset;
            startHtmlOffset = focusHtmlOffset;
            endTextOffset = anchorTextOffset;
            endHtmlOffset = anchorHtmlOffset;

        }
        else{
            startTextOffset = anchorTextOffset;
            startHtmlOffset = anchorHtmlOffset;
            endTextOffset = focusTextOffset;
            endHtmlOffset = focusHtmlOffset;
        }
        let highlight: HighlightObject = {
            id: `span ${localStorage.length + 1}`,
            textStartPos: startTextOffset,
            textEndPos: endTextOffset,
            text: text.substring(startTextOffset, endTextOffset),
            caption: caption,
            htmlStartPos: startHtmlOffset + startTextOffset,
            htmlEndPos: endTextOffset + endHtmlOffset
        }
        localStorage.setItem(highlight.id, JSON.stringify(highlight));
        addHighlight(highlight);
        addCaption(highlight);


        for(let id = 1;id <= localStorage.length;id++){
            document.getElementById(`span ${id}`)?.addEventListener('mouseover',spanHover);
            document.getElementById(`span ${id}`)?.addEventListener('mouseout',spanHover);
        }
    }

    let highlightArea = null;
    onMount(() => {
        highlightArea = document.getElementById("highlightarea");
    });

    let prevText = null;
    const onTextChange = (text) => {
        if (prevText) {
            // Moving on to new text.
            localStorage.clear()
        }
        prevText = text;

        highlightArea.textContent = text;

        let highlights = getHighlights();
        highlights.sort((a,b)=>{
            return a.id < b.id?-1:a.id == b.id?0:1;
        })
        for(let i = 0;i < highlights.length;i++){
            addHighlight(highlights[i]);
            addCaption(highlights[i]);
        }
        for(let id = 1;id <= localStorage.length;id++){
            document.getElementById(`span ${id}`)?.addEventListener('mouseover',spanHover);
            document.getElementById(`span ${id}`)?.addEventListener('mouseout',spanHover);
        }
    }

    $: highlightArea && onTextChange(text);

    /**
     * Retrives all highlights from localstorage and presents them as an array
     */
    export function getHighlights(): HighlightObject[]{
        let highlights: HighlightObject[] = []
        for(let i = 0;i < localStorage.length;i++){
            highlights = [...highlights, JSON.parse(localStorage[<string> localStorage.key(i)])]
        }
        return highlights;
    }
</script>

<p on:mouseup={onTextSelect} id="highlightarea" />
<button class="bg-zinc-200 hover:bg-zinc-300 disabled:bg-zinc-100" disabled={busy} on:click={()=>{
    dispatch('highlights', getHighlights());
}}>Submit</button>
