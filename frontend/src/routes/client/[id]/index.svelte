<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import Client from '../../../api/Client';
  import TextCaptioner from '../../../components/textCaptioner.svelte';

  let logs = "Logs:\n";
  let connected = false;
  let working = false;
  let text = "";

  let client = null;
  onMount(() => {
    client = new Client($page.params.id);
    client.listen("ready", () => {
      logs += "Connected.\n";
      connected = true;
      client.ready();
    });
    client.listen("new_task", (taskInfo) => {
      console.log(taskInfo);
      logs += `New task: ${JSON.stringify(taskInfo)}\n`;
      working = true;

      text = taskInfo.text;
    });
    client.listen("task_available", client.ready.bind(client));
    client.listen("error", (error) => {
      logs += error + "\n";
      connected = false;
    });
    client.listen("idle", (error) => {
      text = "";
      logs += "Waiting for new task...\n";
    });
    client.connect();
  });

  const complete = (captions, indices) => {
    const task = { caption_index: indices, captions };
    logs += `Task complete: ${JSON.stringify(task)}\n`
    client.complete(task);
    working = false;
  };

  const handleHighlights = (event) => {
    let highlights = event.detail;

    const captions = highlights.map(({caption}) => caption);
    const captionIndices = highlights.map(({textStartPos, textEndPos}) => [textStartPos, textEndPos]);
    complete(captions, captionIndices);
  };
</script>

<style>
  div.logs {
    margin-top: 8px;
    white-space: pre-line;
    background: black;
    color: white;
  }
</style>

<h1 class="text-xl">Welcome to CHEESE!</h1>
<h2>Your client ID is {$page.params.id}.</h2>

<TextCaptioner text={text} busy={!working} on:highlights={handleHighlights} />
<div class="logs">{logs}</div>
