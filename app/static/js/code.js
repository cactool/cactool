const SOCIAL_MEDIA = "SOCIAL_MEDIA"
const BOOLEAN = "BOOLEAN"
const HIDDEN = "HIDDEN"
const LIKERT = "LIKERT"

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
    if (row.is_empty){
        window.location.replace(`/dataset/${window.dataset_id}/nomore`)
        return;
    }
    window.row_number = row.row_number
    var columns = row.columns
    for (const [column_id, data] of Object.entries(columns)){ 
        id = "column-" + column_id
        if (data.type === SOCIAL_MEDIA){
            social_media_embed(data.value, id, column_id)
        }
        else if (data.type == BOOLEAN) {
            checkbox(data.prompt, data.value === "true", id)
        }
        else if (data.type == HIDDEN) {
            hidden(data.prompt, data.value, id)
        }
        else if (data.type == LIKERT) {
            likert(data.prompt, data.value, id)
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
        console.log(column.type)
        if(column.type === SOCIAL_MEDIA || column.type === HIDDEN){
            continue
        }
        else if(column.type == LIKERT){
            data.values[column.name] = document.querySelector(`input[name="options-${id}"]:checked`).value;
        }
        else{
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

function skip(){
    data = {
        dataset_id: window.dataset_id,
        row_number: window.row_number,
        skip: true,
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

function post_unavailable(){
    data = {
        dataset_id: window.dataset_id,
        row_number: window.row_number,
        post_unavailable: true,
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

function sanitise(string) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        "/": '&#x2F;',
    };
    const regex = /[&<>"'/]/ig;
    return string.replace(
        regex,
        match => map[match]
    );
  }

function input(column_name, value, id) {
            document.getElementById(id).innerHTML = `
                <div class="input-group">
                    <div class="input-group-prepend col-6">
                        <span class="input-group-text col-12"> ${sanitise(column_name)} </span>
                    </div>
                    <input class="form-control" value='${sanitise(value)}'>
                </div>
            `
}

function checkbox(column_name, value, id) {
            document.getElementById(id).innerHTML = `
                <div class="input-group">
                    <div class="input-group-prepend col-6">
                        <span class="input-group-text col-12"> ${sanitise(column_name)} </span>
                    </div>

                    <input id=check-${id} class="btn-check" type=checkbox ${value? 'checked' : ''}>
                    <label for=check-${id} class="btn btn-outline-primary"> Yes </label>
                </div>
            `
}

function likert(column_name, value, id) {
    document.getElementById(id).innerHTML = `
        <div class="input-group">
            <div class="input-group-prepend col-6">
                <span class="input-group-text col-12"> ${sanitise(column_name)} </span>
            </div>
             
            <label for="option1-${id}" class="l15">
                Didn't like
                <br>
                <input type="radio" name="options-${id}" id="$option1-${id}" autocomplete="off" value="1">
            </label>

            <label class="l15" for="option2-${id}">
                Tolerable
                <br>
                <input type="radio" name="options-${id}" id="option2-${id}" autocomplete="off" value="2">
            </label>

            <label for="option3-${id}" class="l15">
                Liked
                <br>
                <input type="radio" name="options-${id}" id="option3-${id}" autocomplete="off" value="3">
            </label>

            <label for="option4-${id}" class="l15">
                Liked a lot
                <br>
                <input type="radio" name="options-${id}" id="option4-${id}" autocomplete="off" value="4">
            </label>
        
            <label for="option5-${id}" class="l15">
                Loved
                <br>
                <input type="radio" name="options-${id}" id="option5-${id}" autocomplete="off" value="5">
            </label>
        </div>
    `
    document.querySelecto(`input[name="options-${id}"][value=${value}]`).checked = true;

}

function hidden(_column_name, _value, id) {
    document.getElementById(id).innerHTML = ``
}

function clear(id){
    document.getElementById(id).innerHTML = "";
}

function social_media_embed(url, id, column_id){
    hostname = new URL(url).hostname
    if (hostname.endsWith("twitter.com"))
        twitter_embed(url, id)
    else if (hostname.endsWith("tiktok.com"))
        tiktok_embed(url, id, column_id)
    else if (hostname.endsWith("instagram.com"))
        instagram_embed(url, id)
}

function tiktok_embed(url, id, column_id) {
    fetch(
        `/dataset/code/tiktok/${window.dataset_id}/${window.row_number}/${column_id}`,
        {
            method: "GET"
        }
    )
    .then(response => response.json())
    .then(
        function(data){
            div = document.createElement("div")
            div.innerHTML = data["html"]
            document.getElementById(id).appendChild(div)
        }
    )
}

function twitter_embed(url, id) {
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