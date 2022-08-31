<script>
  import { goto } from '$app/navigation';
  let clientID = "";
</script>

<h1 class="text-xl">Welcome to CHEESE!</h1>
<p>Obtain a client ID to start.</p>

<p>Already have a client ID? Enter it here:</p>
<form on:submit|preventDefault={goto(`/client/${clientID}`)}>
  <input type="text" bind:value={clientID} class="bg-zinc-200" />
  <button disabled={!clientID} class="bg-black text-white disabled:bg-zinc-500">Go</button>
</form>
