<script type="ts">
    import Test from './test.svelte';

    function handleHighlights(event:any){
        let highlights = event.detail;
        console.log("Recieved highlights", highlights);
    }

</script>
<h1 class="text-xl">Welcome to Cheese!</h1>
<Test on:highlights={handleHighlights}/>