<script lang="ts">
  import { toast } from 'svelte-sonner';
  import { onMount, getContext, createEventDispatcher } from 'svelte';
  import { marked } from 'marked';
  const i18n = getContext('i18n');
  const dispatch = createEventDispatcher();
  import markedExtension from '$lib/utils/marked/extension';
  import markedKatexExtension from '$lib/utils/marked/katex-extension';
  import { mentionExtension } from '$lib/utils/marked/mention-extension';
  import { centerExtension } from '$lib/utils/marked/center-extension';
  import 'katex/dist/katex.min.css';

  import { artifactCode, chatId, settings, showArtifacts, showControls } from '$lib/stores';
  import { copyToClipboard, createMessagesList } from '$lib/utils';

  import XMark from '../icons/XMark.svelte';
  import ArrowsPointingOut from '../icons/ArrowsPointingOut.svelte';
  import Tooltip from '../common/Tooltip.svelte';
  import SvgPanZoom from '../common/SvgPanZoom.svelte';
  import Download from '../icons/Download.svelte';
  import DocumentPage from '../icons/DocumentPage.svelte';
  import MarkdownTokens from '$lib/components/chat/Messages/Markdown/MarkdownTokens.svelte';

  export let saveMessage: (id: string, message: { content: string }) => Promise<void>;
  export let overlay = false;
  export let history: { currentId: string; messages: Record<string, { content: string; role: string }> };
  let messages: { role: string; content: string }[] = [];

  let contents: Array<{
    type: string;
    content: string | any[];
    sourceCode?: string;
    editableCode?: string;
  }> = [];
  let selectedContentIdx = 0;
  let viewMode: 'preview' | 'code' = 'preview';

  let copied = false;
  let iframeElement: HTMLIFrameElement;
  let codeTextarea: HTMLTextAreaElement;
  let isEdited = false;

  const options = {
    throwOnError: false,
    breaks: true
  };

  marked.use(markedKatexExtension(options));
  marked.use(markedExtension(options));
  marked.use({
    extensions: [
      mentionExtension({ triggerChar: '@' }),
      mentionExtension({ triggerChar: '#' }),
      centerExtension()
    ]
  });

  $: if (history) {
    messages = createMessagesList(history, history.currentId);
    getContents();
  } else {
    messages = [];
    getContents();
  }
function extractArtifactsFromMessage(message: string) {
  const tokens = marked.lexer(message);

  let html = "";
  let css = "";
  let js = "";
  let markdown = "";
  let codeBlocks: { lang: string; code: string }[] = [];

  for (const token of tokens) {
    if (token.type === "code") {
      const lang = (token.lang || "").toLowerCase();
      const code = token.text;

      if (lang === "html") html += code + "\n";
      else if (lang === "css") css += code + "\n";
      else if (lang === "js" || lang === "javascript") js += code + "\n";
      else if (lang === "markdown" || lang === "md") markdown += code + "\n";
      else codeBlocks.push({ lang, code });

    } else if (token.type === "html") {
      // Inline HTML content
      html += token.text + "\n";

    } else {
      // All non-code tokens belong to markdown content
      if (token.raw) markdown += token.raw;
      else if (token.text) markdown += token.text;
    }
  }

  return { html, css, js, markdown, codeBlocks };
}
const getContents = () => {
  contents = [];

  messages.forEach((message) => {
    if (message?.role !== "user" && message?.content) {
      const {
        html: htmlContent,
        css: cssContent,
        js: jsContent,
        markdown: markdownContent,
        codeBlocks
      } = extractArtifactsFromMessage(message.content);

      // ----------------------------------------------------------------------
      // 1. Render HTML/CSS/JS → IFRAME ARTIFACT
      // ----------------------------------------------------------------------
      if (htmlContent || cssContent || jsContent) {
        const fullHtml = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <${''}style>
body {
    background-color: white;
}
${cssContent}
    </${''}style>
</head>
<body>
${htmlContent}
    <${''}script>
${jsContent}
    </${''}script>
</body>
</html>`;

        contents = [
          ...contents,
          {
            type: "iframe",
            content: fullHtml,
            sourceCode: fullHtml,
            editableCode: fullHtml
          }
        ];

        return;
      }

      // ----------------------------------------------------------------------
      // 2. Markdown Artifact
      // ----------------------------------------------------------------------
      if (markdownContent.trim() !== "") {
        const tokens = marked.lexer(markdownContent);

        contents = [
          ...contents,
          {
            type: "markdown",
            content: tokens,
            sourceCode: markdownContent,
            editableCode: markdownContent
          }
        ];

        return;
      }

      // ----------------------------------------------------------------------
      // 3. SVG or generic code blocks
      // ----------------------------------------------------------------------
      for (const block of codeBlocks) {
        if (block.lang === "svg" || (block.lang === "xml" && block.code.includes("<svg"))) {
          contents = [
            ...contents,
            {
              type: "svg",
              content: block.code,
              sourceCode: block.code,
              editableCode: block.code
            }
          ];
          continue;
        }
      }
    }
  });

  if (contents.length === 0) {
    showControls.set(false);
    showArtifacts.set(false);
  }

  selectedContentIdx = contents.length > 0 ? contents.length - 1 : 0;
  isEdited = false;
};



	function navigateContent(direction: 'prev' | 'next') {
		selectedContentIdx =
			direction === 'prev'
				? Math.max(selectedContentIdx - 1, 0)
				: Math.min(selectedContentIdx + 1, contents.length - 1);
		isEdited = false;
	}
  const handleCodeChange = (event: Event) => {
    const target = event.target as HTMLTextAreaElement;
    const newCode = target.value;

    if (contents[selectedContentIdx]) {
      contents[selectedContentIdx].editableCode = newCode;
      isEdited = newCode !== contents[selectedContentIdx].sourceCode;

      if (contents[selectedContentIdx].type === 'markdown') {
        contents[selectedContentIdx].content = marked.lexer(newCode);
      } else if (contents[selectedContentIdx].type === 'iframe') {
        contents[selectedContentIdx].content = newCode;
      } else if (contents[selectedContentIdx].type === 'svg') {
        contents[selectedContentIdx].content = newCode;
      }

      contents = [...contents];
    }
  };

  const resetCode = () => {
    if (contents[selectedContentIdx]) {
      contents[selectedContentIdx].editableCode = contents[selectedContentIdx].sourceCode;
      contents[selectedContentIdx].content = contents[selectedContentIdx].type === 'markdown'
        ? marked.lexer(contents[selectedContentIdx].sourceCode || '')
        : contents[selectedContentIdx].sourceCode;
      isEdited = false;
      contents = [...contents];
    }
  };

  async function saveCode(
    selectedContentIdx: number,
    contents: { editableCode: string; sourceCode: string; type: string }[],
    history: { currentId: string; messages: Record<string, { content: string }> },
    saveMessage: (id: string, message: { content: string }) => Promise<void>
  ) {
    if (!history || !history.messages) return;

    const currentId = history.currentId;
    if (!currentId || !history.messages[currentId]) return;

    let updatedContent = contents[selectedContentIdx].editableCode;

    if (contents[selectedContentIdx].type === 'markdown') {
      updatedContent = `\`\`\`markdown\n${updatedContent}\n\`\`\``;
    }

    history.messages[currentId].content = updatedContent;
    contents[selectedContentIdx].sourceCode = contents[selectedContentIdx].editableCode;
    isEdited = false;

    console.log('Saving to backend:', history.messages[currentId]);

    if (saveMessage) {
      await saveMessage(currentId, { content: updatedContent });
      toast.success('Saved successfully!');
    } else {
      console.warn('saveMessage is not provided.');
    }
  }

  const iframeLoadHandler = () => {
    iframeElement.contentWindow.addEventListener(
      'click',
      function (e) {
        const target = e.target.closest('a');
        if (target && target.href) {
          e.preventDefault();
          const url = new URL(target.href, iframeElement.baseURI);
          if (url.origin === window.location.origin) {
            iframeElement.contentWindow.history.pushState(
              null,
              '',
              url.pathname + url.search + url.hash
            );
          } else {
            console.info('External navigation blocked:', url.href);
          }
        }
      },
      true
    );

    iframeElement.contentWindow.addEventListener('mouseenter', function (e) {
      e.preventDefault();
      iframeElement.contentWindow.addEventListener('dragstart', (event) => {
        event.preventDefault();
      });
    });
  };

	const showFullScreen = () => {
		if (iframeElement.requestFullscreen) {
			iframeElement.requestFullscreen();
		} else if (iframeElement.webkitRequestFullscreen) {
			iframeElement.webkitRequestFullscreen();
		} else if (iframeElement.msRequestFullscreen) {
			iframeElement.msRequestFullscreen();
		}
	};

  const downloadArtifact = () => {
    const artifact = contents[selectedContentIdx];
    const isMarkdown = artifact.type === 'markdown';
    const content = isMarkdown ? artifact.editableCode ?? artifact.sourceCode : artifact.content;

    const blob = new Blob([content], {
      type: isMarkdown ? 'text/markdown;charset=utf-8' : 'text/html;charset=utf-8',
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `artifact-${$chatId}-${selectedContentIdx}.${isMarkdown ? 'md' : 'html'}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadAndConvertToDocx = async () => {
    try {
      const artifact = contents[selectedContentIdx];
      const markdownContent = artifact.editableCode ?? artifact.sourceCode;

      const blob = new Blob([markdownContent], { type: 'text/markdown' });
      const formData = new FormData();
      formData.append('file', blob, `artifact-${$chatId}-${selectedContentIdx}.md`);

      const response = await fetch('http://localhost:8080/convert-md-to-docx', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Conversion failed with status ${response.status}`);
      }

      const docxBlob = await response.blob();
      const url = URL.createObjectURL(docxBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `artifact-${$chatId}-${selectedContentIdx}.docx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error converting Markdown to DOCX via API:', error);
    }
  };

  const copyCurrentContent = () => {
    const content = viewMode === 'code'
      ? contents[selectedContentIdx].editableCode || contents[selectedContentIdx].content
      : contents[selectedContentIdx].content;
    copyToClipboard(content);
    copied = true;
    setTimeout(() => {
      copied = false;
    }, 2000);
  };

  const autoResize = (textarea: HTMLTextAreaElement) => {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
  };

  onMount(() => {
    artifactCode.subscribe((value) => {
      if (contents) {
        const codeIdx = contents.findIndex((content) => content.content.includes(value));
        selectedContentIdx = codeIdx !== -1 ? codeIdx : 0;
      }
    });
  });
</script>

<div class="w-full h-full relative flex flex-col bg-white dark:bg-gray-850" id="artifacts-container">
  <div class="w-full h-full flex flex-col flex-1 relative">
    {#if contents.length > 0}
      <div class="pointer-events-auto z-20 flex justify-between items-center p-2.5 font-primary text-gray-900 dark:text-white">
        <div class="flex-1 flex items-center justify-between pr-1">
          <div class="flex items-center space-x-2">
            <div class="flex items-center gap-0.5 self-center min-w-fit" dir="ltr">
              <button
                class="self-center p-1 hover:bg-black/5 dark:hover:bg-white/5 dark:hover:text-white hover:text-black rounded-md transition disabled:cursor-not-allowed"
                on:click={() => navigateContent('prev')}
                disabled={contents.length <= 1}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="2.5"
                  class="size-3.5"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M15.75 19.5 8.25 12l7.5-7.5"
                  />
                </svg>
              </button>
              <div class="text-xs self-center dark:text-gray-100 min-w-fit">
                {$i18n.t('Version {{selectedVersion}} of {{totalVersions}}', {
                  selectedVersion: selectedContentIdx + 1,
                  totalVersions: contents.length
                })}
                {#if isEdited}
                  <span class="text-orange-500 ml-1">•</span>
                {/if}
              </div>
              <button
                class="self-center p-1 hover:bg-black/5 dark:hover:bg-white/5 dark:hover:text-white hover:text-black rounded-md transition disabled:cursor-not-allowed"
                on:click={() => navigateContent('next')}
                disabled={contents.length <= 1}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="2.5"
                  class="size-3.5"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="m8.25 4.5 7.5 7.5-7.5 7.5"
                  />
                </svg>
              </button>
            </div>

			
						<!-- Code/Preview Toggle Buttons -->
            <div class="flex items-center bg-gray-100 dark:bg-gray-800 rounded-md p-0.5">
              <button
                class="text-xs px-2 py-1 rounded transition-colors {viewMode === 'code'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'}"
                on:click={() => (viewMode = 'code')}
              >
                {$i18n.t('Code')}
              </button>
              <button
                class="text-xs px-2 py-1 rounded transition-colors {viewMode === 'preview'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'}"
                on:click={() => (viewMode = 'preview')}
              >
                {$i18n.t('Preview')}
              </button>
            </div>
            {#if isEdited && viewMode === 'code'}
              <button
                class="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded transition-colors"
                on:click={resetCode}
              >
                {$i18n.t('Reset')}
              </button>
              <button
                class="text-xs px-2 py-1 bg-green-100 hover:bg-green-200 dark:bg-green-700 dark:hover:bg-green-600 text-green-800 dark:text-green-200 rounded transition-colors"
                on:click={() => saveCode(selectedContentIdx, contents, history, saveMessage)}
              >
                {$i18n.t('Save')}
              </button>
            {/if}
          </div>



          <div class="flex items-center gap-1.5">
            <button
              class="copy-code-button bg-none border-none text-xs bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-md px-1.5 py-0.5"
              on:click={copyCurrentContent}
            >
              {copied ? $i18n.t('Copied') : $i18n.t('Copy')}
            </button>
            <Tooltip content={$i18n.t('Download')}>
              <button
                class="bg-none border-none text-xs bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-md p-0.5"
                on:click={downloadArtifact}
              >
                <Download className="size-3.5" />
              </button>
            </Tooltip>
            <Tooltip content={$i18n.t('Downloadindocx')}>
              <button
                class="bg-none border-none text-xs bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-md p-0.5"
                on:click={downloadAndConvertToDocx}
              >
                <DocumentPage className="size-3.5" />
              </button>
            </Tooltip>
            {#if contents[selectedContentIdx].type === 'iframe' && viewMode === 'preview'}
              <Tooltip content={$i18n.t('Open in full screen')}>
                <button
                  class="bg-none border-none text-xs bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-md p-0.5"
                  on:click={showFullScreen}
                >
                  <ArrowsPointingOut className="size-3.5" />
                </button>
              </Tooltip>
            {/if}
          </div>
        </div>

        <button
          class="self-center pointer-events-auto p-1 rounded-full bg-white dark:bg-gray-850"
          on:click={() => {
            dispatch('close');
            showControls.set(false);
            showArtifacts.set(false);
          }}
        >
          <XMark className="size-3.5 text-gray-900 dark:text-white" />
        </button>
      </div>
    {/if}
    {#if overlay}
      <div class="absolute top-0 left-0 right-0 bottom-0 z-10"></div>
    {/if}
    <div class="flex-1 w-full h-full">
      <div class="h-full flex flex-col">
        {#if contents.length > 0}
          <div class="max-w-full w-full h-full">
            {#if viewMode === 'code'}
              <div class="w-full h-full bg-gray-50 dark:bg-gray-900 overflow-hidden relative">
                <textarea
                  bind:this={codeTextarea}
                  bind:value={contents[selectedContentIdx].editableCode}
                  on:input={handleCodeChange}
                  on:input={(e) => autoResize(e.target)}
                  class="w-full h-full p-4 text-sm font-mono text-gray-800 dark:text-gray-200 bg-transparent border-0 outline-none resize-none whitespace-pre"
                  style="font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; tab-size: 2;"
                  spellcheck="false"
                  placeholder={$i18n.t('Edit your code here...')}
                ></textarea>
              </div>
            {:else if contents[selectedContentIdx].type === 'iframe'}
              <iframe
                bind:this={iframeElement}
                title="Content"
                srcdoc={contents[selectedContentIdx].content}
                class="w-full border-0 h-full rounded-none"
                sandbox="allow-scripts allow-downloads{($settings?.iframeSandboxAllowForms ?? false)
                  ? ' allow-forms'
                  : ''}{($settings?.iframeSandboxAllowSameOrigin ?? false)
                  ? ' allow-same-origin'
                  : ''}"
                on:load={iframeLoadHandler}
              ></iframe>
            {:else if contents[selectedContentIdx].type === 'svg'}
              <SvgPanZoom
                className="w-full h-full max-h-full overflow-hidden"
                svg={contents[selectedContentIdx].content}
              />
            {:else if contents[selectedContentIdx].type === 'markdown'}
              <div class="w-full h-full overflow-auto p-4 prose dark:prose-invert max-w-none">
                <MarkdownTokens
                  id={`artifact-${selectedContentIdx}`}
                  tokens={contents[selectedContentIdx].content}
                  done={true}
                  save={false}
                  preview={false}
                  editCodeBlock={false}
                  topPadding={false}
                  onTaskClick={() => {}}
                  onSourceClick={() => {}}
                  onSave={() => {}}
                  onUpdate={() => {}}
                  onPreview={() => {}}
                />
              </div>
            {/if}
          </div>
        {:else}
          <div class="m-auto font-medium text-xs text-gray-900 dark:text-white">
            {$i18n.t('No HTML, CSS, JavaScript, or Markdown content found.')}
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>