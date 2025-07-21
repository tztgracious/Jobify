1. Start FastAPI
2. Send query and fetch response:
   ```
   async function get_response() {
    const response = await fetch("http://localhost:8000/search/local?query=gold price today")
    if (response.ok) {
        const resjson = await response.json()
        const cleaned = resjson["response"].replace(/\[Data:.*?\]/g, "").trim().replace(/\s+\./g, ".")
        console.log(cleaned)
    }
   }     
   ```
