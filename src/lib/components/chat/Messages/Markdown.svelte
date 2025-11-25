<script>
    import { marked } from 'marked';
    import { replaceTokens, processResponseContent } from '$lib/utils';
    import { user } from '$lib/stores';

    import markedExtension from '$lib/utils/marked/extension';
    import markedKatexExtension from '$lib/utils/marked/katex-extension';
    import { disableSingleTilde } from '$lib/utils/marked/strikethrough-extension';
    import { mentionExtension } from '$lib/utils/marked/mention-extension';
    import { centerExtension } from '$lib/utils/marked/center-extension';
    import footnoteExtension from '$lib/utils/marked/footnote-extension';
    import citationExtension from '$lib/utils/marked/citation-extension';

    import MarkdownTokens from './Markdown/MarkdownTokens.svelte';

    export let id = '';
    export let content;
    export let done = true;
    export let model = null;
    export let save = false;
    export let preview = false;

    export let editCodeBlock = true;
    export let topPadding = false;

    export let sourceIds = [];

    export let onSave = () => {};
    export let onUpdate = () => {};

    export let onPreview = () => {};

    export let onSourceClick = () => {};
    export let onTaskClick = () => {};

    let tokens = [];

    const options = {
        throwOnError: false,
        breaks: true
    };

    marked.use(markedKatexExtension(options));
    marked.use(markedExtension(options));
    marked.use(citationExtension(options));
    marked.use(footnoteExtension(options));
    marked.use(disableSingleTilde);
    marked.use({
        extensions: [
            mentionExtension({ triggerChar: '@' }),
            mentionExtension({ triggerChar: '#' }),
            centerExtension()
        ]
    });

    /**
     * Pre-processes the markdown string to handle nested code blocks.
     * specifically looks for ```markdown blocks that contain internal code blocks
     * and wraps the outer block in 4 backticks (````) to prevent parsing errors.
     */
    const preprocessMarkdown = (text) => {
        if (!text) return text;

        // Regex Breakdown:
        // 1. (```markdown)      -> Matches outer start tag
        // 2. ([\s\S]*?)         -> Matches content before inner block
        // 3. (```[\w]*)         -> Matches inner block start tag (e.g. ```python)
        // 4. ([\s\S]*?)         -> Matches content inside inner block
        // 5. (```)              -> Matches inner block closing tag
        // 6. ([\s\S]*?)         -> Matches content after inner block
        // 7. (```)              -> Matches outer closing tag
        const nestedRegex = /(```markdown)([\s\S]*?)(```[\w]*)([\s\S]*?)(```)([\s\S]*?)(```)/g;

        return text.replace(nestedRegex, (match, start, p1, innerStart, p2, innerEnd, p3, outerEnd) => {
            // Reconstruct the block but wrap the whole thing in 4 backticks (````)
            // We leave the inner content strictly as is.
            return `\`\`\`\`markdown${p1}${innerStart}${p2}${innerEnd}${p3}\`\`\`\``;
        });
    };

    $: (async () => {
        if (content) {
            // 1. Process user/model tokens
            let processedContent = replaceTokens(processResponseContent(content), model?.name, $user?.name);
            
            // 2. Fix nested markdown blocks before parsing
            processedContent = preprocessMarkdown(processedContent);

            // 3. Generate tokens
            tokens = marked.lexer(processedContent);
        }
    })();
</script>

{#key id}
    <MarkdownTokens
        {tokens}
        {id}
        {done}
        {save}
        {preview}
        {editCodeBlock}
        {sourceIds}
        {topPadding}
        {onTaskClick}
        {onSourceClick}
        {onSave}
        {onUpdate}
        {onPreview}
    />
{/key}