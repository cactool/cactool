const SOCIAL_MEDIA = "SOCIAL_MEDIA"
const BOOLEAN = "BOOLEAN"
const HIDDEN = "HIDDEN"
const LIKERT = "LIKERT"
const ONE_TO_SEVEN = "ONE_TO_SEVEN"
const ONE_TO_FIVE = "ONE_TO_FIVE"
const ONE_TO_THREE = "ONE_TO_THREE"
const DISPLAY = "DISPLAY"

const ORDINAL_LOOKUP = {
    [ONE_TO_THREE]: 3,
    [ONE_TO_FIVE]: 5,
    [ONE_TO_SEVEN]: 7
}

const TWITTER_HOSTS = [
  "twitter.com",
  "www.twitter.com",
]

const INSTAGRAM_HOSTS = [
  "instagram.com",
  "www.instagram.com"
]


function next_row() {
    fetch(
        "/dataset/nextrow",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(
                {
                    dataset_id: window.dataset_id,
                }
            )
        }
    ).then(response => response.json()).then(update_row)
}

function fetch_row(row_number) {
    fetch(
        `/dataset/row`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(
                {
                    dataset_id: window.dataset_id,
                    row_number: row_number,
                }
            )
        }
    ).then(response => response.json()).then(update_row)
}

function update_row(row){
    if (row.is_empty){
        window.location.replace(`/dataset/${window.dataset_id}/nomore`)
        return;
    }
    window.row_number = row.row_number
    document.getElementById("row-name").innerText = row.row_number + 1;
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
        else if (
            data.type == ONE_TO_THREE
            || data.type == ONE_TO_FIVE
            || data.type == ONE_TO_SEVEN
        ) {
            numerical_ordinal(data.prompt, data.value, id, ORDINAL_LOOKUP[data.type])
        }
        else if (data.type == DISPLAY) {
            display(data.prompt, data.value, id)
        }
        else {
            input(data.prompt, data.value, id)
        }
    }
}

function get_value(column_name){
    id = "column-" + column_name
    return document.getElementById(id).getElementsByTagName("input")[0].value
}

function get_boolean(column_name){
    id = "column-" + column_name
    return document.getElementById(id).getElementsByTagName("input")[0].checked
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
        else if(
            column.type == LIKERT
            || column.type == ONE_TO_THREE
            || column.type == ONE_TO_FIVE
            || column.type == ONE_TO_SEVEN){
            try{
                data.values[column.name] = document.querySelector(`input[name="options-column-${column.name}"]:checked`).value;
            }
            catch(exception){
                if (exception instanceof TypeError) {
                    data.values[column.name] = ""
                }
                else{
                    console.log(exception)
                }
            }
        }
        else if (column.type == BOOLEAN){
            data.values[column.name] = get_boolean(column.name);
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

function go_to_row() {
    const input_field = document.getElementById("row-number");
    console.log(input_field);
    fetch_row(input_field.value)
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

function es(string) {
    const map = {
        '\\': '\\\\',
        '"': '\\"',
        "'": '\\\';',
        '\n': '',
        '\r': ''
    };
    const regex = /[\\"'\n\r]/ig;
    return string.replace(
        regex,
        match => map[match]
    );
}

function input(column_name, value, id) {
            document.getElementById(id).innerHTML = `
                <div class="input-group">
                    <input class="form-control" value='${sanitise(value)}'>
                </div>
            `
}

function display(column_name, value, id) {
            document.getElementById(id).innerHTML = `
                <div>
                    <p class="information">${sanitise(value)}</p>
                </div>
            `
}

function checkbox(column_name, value, id) {
            document.getElementById(id).innerHTML = `
                <div class="input-group">
                    <input id=check-${id} class="btn-check" type=checkbox ${value? 'checked' : ''}>
                    <label for=check-${id} class="btn btn-outline-primary"> Yes </label>
                </div>
            `
}

function likert(column_name, value, id) {
    document.getElementById(id).innerHTML = `
        <div class="input-group multi-choice">
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
    try {
        document.querySelector(`input[name="options-${id}"][value="${es(value)}"]`).checked = true;
    }
    catch (exception) {
        if (exception instanceof TypeError){
            
        }
        else{
            console.log(exception)
        }
    }

}

function numerical_ordinal(column_name, value, id, number) {
    html = `
        <div class="input-group multi-choice">
    `
    
    for (i = 0; i < number; i++){
        html += `
            <label for="option${i + 1}-${id}" class="l15">
                ${i + 1} 
                <br>
                <input type="radio" name="options-${id}" id="option${i + 1}-${id}" autocomplete="off" value="${i + 1}">
            </label>
    `
    }
    html += "</div>"
    document.getElementById(id).innerHTML = html
    try {
        document.querySelector(`input[name="options-${id}"][value="${es(value)}"]`).checked = true;
    }
    catch (exception){
        if (exception instanceof TypeError){

        }
        else {
            console.log(exception)
        }
    }

}

function hidden(_column_name, _value, id) {
}

function clear(id){
    document.getElementById(id).innerHTML = "";
}

function social_media_embed(url, id, column_id){
    host = new URL(url).host
    if (TWITTER_HOSTS.includes(host)) {
        twitter_embed(url, id);
    }
    else if (INSTAGRAM_HOSTS.includes(host)) {
        instagram_embed(url, id, column_id);
    }
    else {
        oembed(url, id, column_id);
    }
}

function instagram_embed(_url, id, column_id){
    iframe = document.createElement("iframe")
    iframe.setAttribute("src", `/dataset/code/instagram/${window.dataset_id}/${window.row_number}/${column_id}`)
    iframe.style.width = "100%"
    iframe.style.height = "100vh"
    document.getElementById(id).appendChild(iframe)
}


function oembed(_url, id, column_id){
    fetch(
        `/dataset/code/oembed/${window.dataset_id}/${window.row_number}/${column_id}`,
        {
            method: "GET"
        }
    )
    .then(response => response.json())
    .then(
        function(data){
            div = document.createElement("div")
            div.innerHTML = data["html"]
            document.getElementById(id).replaceChildren(div)
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

function initialise(dataset_id, columns, types) {
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
    next_row()
}
