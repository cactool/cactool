const SOCIAL_MEDIA = "SOCIAL_MEDIA"

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

function update_row(row){
    window.row_number = row.row_number
    var columns = row.columns
    for (const [column_id, data] of Object.entries(columns)){ 
        id = "column-" + column_id
        if (data.type === SOCIAL_MEDIA){
            twitter_embed(data.value, id)
        }
        else {
            input(data.prompt, data.value, id)
        }
        // document.getElementById("column-" + column_name).innerHTML = value
    }
}

function get_value(column_name){
    id = "column-" + column_name
    return document.getElementById(id).getElementsByTagName("input")[0].value
}

function submit(){
    data = {
        dataset_id: window.dataset_id,
        row_number: window.row_number,
        values: {}
    } 
    
    for (column of window.columns) {
        if(column.type !== SOCIAL_MEDIA){
            data.values[column.name] = get_value(column.name)
        }

    }
    
    fetch(
        `/dataset/code/${ window.dataset_id }`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        }
    ).then(next_row)
}

function input(column_name, value, id) { /******* TODO: SANITISE ME!!!! *********/
            document.getElementById(id).innerHTML = `
                <div class="input-group">
                    <div class="input-group-prepend col-6">
                        <span class="input-group-text col-12"> ${column_name} </span>
                    </div>
                    <input class="form-control" value='${value}'>
                </div>
            `
}

function clear(id){
    document.getElementById(id).innerHTML = "";
}

function twitter_embed(url, id) { /* TODO: Change to disallow arbitrary twitter urls */
        clear(id)
        twttr.widgets.createTweet(
            url.split("/").at(-1),
            document.getElementById(id),
            {
                align: "center"
            }
        )
}

function update_next_row(dataset_id){
    fetch_next_row(dataset_id, update_row)
}

function next_row(){
    update_next_row(window.dataset_id)
}

function initialise(dataset_id, columns, types) {
    update_next_row(dataset_id)
    window.dataset_id = dataset_id
    window.column_names = columns
    window.column_types = types
    window.columns = window.column_names.map(
        function(column_name, index) {
            return {
                name: column_name,
                type: window.column_types[index]
            }
        } 
    )
}