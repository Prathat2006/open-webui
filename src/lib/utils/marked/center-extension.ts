// center-extension.ts

function centerStart(src: string) {
    // Find start of potential '% ' at line beginning
    const match = src.match(/^% /);
    return match ? match.index : -1;
}

function centerTokenizer(src: string, tokens: any[]) {
    // Match line starting with '% ' followed by text
    const re = /^% (.*)/;
    const match = re.exec(src);
    if (!match) return;

    const text = match[1].trim();

    const token = {
        type: 'center',
        raw: match[0],
        text: text,
        tokens: []  // Will hold inline-parsed tokens
    };

    // Parse inline Markdown in the text (e.g., bold, links)
    this.lexer.inline(text, token.tokens);

    return token;
}

function centerRenderer(token: any) {
    // Unused (custom rendering in Svelte), but include for completeness
    return `<h1 style="text-align: center;">${this.parser.parseInline(token.tokens)}</h1>`;
}

export function centerExtension() {
    return {
        name: 'center',
        level: 'block',  // Block-level for titles
        start: centerStart,
        tokenizer: centerTokenizer,
        renderer: centerRenderer
    };
}