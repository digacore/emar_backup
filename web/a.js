const count = 1;

function brudTest() {
    const promises = Array.from({ length: count }, async (_, i) => {

        console.time(`Fetch ${i + 1}`);
        try {

            const response = await fetch('https://app.emarvault.com/pcc_api/download_backup', {
                method: 'POST',
                body: JSON.stringify({
                    computer_name: 'DESKTOP-JE69F1L',
                    identifier_key: '7febd443-fbc1-4a7c-a636-6b824194fe47',
                    pcc_fac_id: '1'
                }),
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            if (!response.ok) {
                const resData = await response.text();
                console.error(`Fetch ${i + 1} failed with response:`, resData);
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            console.log(response)
            console.timeLog(`Fetch ${i + 1}`, 'Response received');
            // const blob = await response.blob();
            // console.log(`Fetch ${i + 1} completed, size: ${blob.size}`);

        } catch (error) {
            console.error(`Fetch ${i + 1} failed:`, error);
        } finally {
            console.timeEnd(`Fetch ${i + 1}`);
        }
    });


    Promise.all(promises)
        .then(() => {
            console.log('All fetches completed');
        })
        .catch(error => {
            console.error('Some fetches failed:', error);
        });

}

brudTest();