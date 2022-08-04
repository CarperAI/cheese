<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import Client from '../../../api/Client';

  let logs = "";
  let connected = false;
  let working = false;

  let client = null;
  onMount(() => {
    client = new Client($page.params.id);
    client.listen("ready", () => {
      logs += "Connected.\n";
      connected = true;
    });
    client.listen("new_task", (taskInfo) => {
      console.log(taskInfo);
      logs += JSON.stringify(taskInfo) + "\n";
      working = true;
    });
    client.listen("task_available", client.ready.bind(client));
    client.listen("error", (error) => {
      logs += error + "\n";
      connected = false;
    });
    client.listen("idle", (error) => {
      logs += "Waiting for new task...\n";
    });
    client.connect();
  });

  const complete = () => {
    client.complete({ caption_index: [[1, 3]], captions: ["This is a caption"] });
    working = false;
  };
</script>

<style>
  div {
    white-space: pre-line;
  }
  button {
    color: white;
    background: black;
  }
  button:disabled {
    background: grey;
  }
</style>

<h1>Page for client with ID {$page.params.id}</h1>
<button on:click={client.ready.bind(client)} disabled={working || !connected}>Ready?</button>
<button on:click={complete} disabled={!working}>Complete</button>
<div>{logs}</div>
