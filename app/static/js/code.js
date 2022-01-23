function fetch_next_row(dataset_id, callback) {
    fetch(
        "/dataset/nextrow",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(
                {
                    dataset_id: dataset_id,
                }
            )
        }
    ).then(response => response.json()).then(callback)
}

function update_row(row_data){
    for (const [column_name, value] of Object.entries(row_data)){ 
        twitter_embed(value, "column-" + column_name)
        // document.getElementById("column-" + column_name).innerHTML = value
    }
}

function twitter_embed(url, id) { /* TODO: Change to disallow arbitrary twitter urls */
        twttr.widgets.createTweet(
            url.split("/").at(-1),
            document.getElementById(id),
            {
                align: "center"
            }
        )
    /* fetch(
        "/embed?url=" + url,
        {
            method: "GET"
        }
    ).then(
        response => response.json()
    ).then(
        json => json["html"]
    ).then(
        html => document.getElementById(id).innerHTML = html
    ) */
}

function update_next_row(dataset_id){
    fetch_next_row(dataset_id, update_row)
}