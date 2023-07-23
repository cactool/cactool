const SOCIAL_MEDIA = "SOCIAL_MEDIA"
const BOOLEAN = "BOOLEAN"
const HIDDEN = "HIDDEN"
const LIKERT = "LIKERT"
const ONE_TO_SEVEN = "ONE_TO_SEVEN"
const ONE_TO_FIVE = "ONE_TO_FIVE"
const ONE_TO_THREE = "ONE_TO_THREE"
const DISPLAY = "DISPLAY"
const IMAGE = "IMAGE"

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

const TIKTOK_HOSTS = [
    "www.tiktok.com",
    "tiktok.com"
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
            checkbox(data.prompt, data.value, id)
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
            numerical_ordinal(column_id, data.value, id, ORDINAL_LOOKUP[data.type])
        }
        else if (data.type == DISPLAY) {
            display(data.prompt, data.value, id)
        }
        else if (data.type == IMAGE) {
            display_image(id, column_id)
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
    const field = document.getElementById("column-" + column_name).querySelector("input:checked");
    return field ? field.value : "";
}

function submit(){
    data = {
        dataset_id: window.dataset_id,
        row_number: window.row_number,
        values: {}
    } 
    
    for (column of window.columns) {
        if(
            column.type === SOCIAL_MEDIA
            || column.type === HIDDEN
            || column.type === IMAGE
            || column.type === DISPLAY) {
            continue
        }
        else if(
            column.type == LIKERT
            || column.type == ONE_TO_THREE
            || column.type == ONE_TO_FIVE
            || column.type == ONE_TO_SEVEN){
            const selected = document.querySelector(`input[name="options-${column.name}"]:checked`);
            data.values[column.name] = selected ? selected.value : "";
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


function input(column_name, value, id) {
    const template = document.getElementById("text-input");
    const field = template.content.cloneNode(true);
    field.querySelector("input").value = value;
    document.getElementById(id).replaceChildren(field);
}

function display(column_name, value, id) {
    const template = document.getElementById("display");
    const field = template.content.cloneNode(true);
    field.querySelector("p").innerText = value;
    document.getElementById(id).replaceChildren(field);
}

function checkbox(column_name, value, id) {
    const template = document.getElementById("yes-no");
    const field = template.content.cloneNode(true);
    [...field.querySelectorAll("input")].forEach(responseField => {
        responseField.name = id;
        if (responseField.value == value) {
            updateRadio(responseField);
        }
    });
    document.getElementById(id).replaceChildren(field);
}

function likert(column_name, value, id) {
    const template = document.getElement("likert");
    const field = template.content.cloneNode(true);
    [...field.querySelectorAll("input")].map(element => {
        element.name = "options-" + id;
        element.id = "option" + element.value + "-" + id;
        if (element.value == value) {
            element.checked = true;
        }
    });
    document.getElementById(id).replaceChildren(field);
}

function numerical_ordinal(column_name, value, id, number) {
    const fieldTemplate = document.getElementById("numerical-ordinal");
    const selectTemplate = document.getElementById("ordinal-select");

    const field = fieldTemplate.content.cloneNode(true);
    for (let index = 0; index < number; index++) {
        const select = selectTemplate.content.cloneNode(true);
        const label = select.querySelector("span");
        const radio = select.querySelector("input");

        label.innerText = index + 1;
        radio.name = "options-" + column_name;
        radio.id = "option" + (index + 1) + "-" + column_name;
        radio.value = index + 1;
        if (radio.value == value) {
            radio.checked = true;
        }
        field.appendChild(select);
    }

    document.getElementById(id).replaceChildren(field);
}

function hidden(_column_name, _value, id) {
}

function social_media_embed(url, id, column_id){
    try {
        host = new URL(url).host;
    }
    catch {
        display_error(id, `Unable to parse URL: ${url}`);
        return;
    }
    if (TWITTER_HOSTS.includes(host)) {
        twitter_embed(url, id);
    }
    else if (INSTAGRAM_HOSTS.includes(host)) {
        instagram_embed(id, column_id);
    }
    else if (TIKTOK_HOSTS.includes(host)) {
        tiktok_embed(id, column_id);
    }

    else {
        oembed(id, column_id);
    }
}

function instagram_embed(id, column_id){
    iframe = document.createElement("iframe")
    iframe.setAttribute("src", `/dataset/code/instagram/${window.dataset_id}/${window.row_number}/${column_id}`)
    iframe.style.width = "70vw"
    iframe.style.height = "100vh"
    document.getElementById(id).replaceChildren(iframe)
}

function tiktok_embed(id, column_id) {
    iframe = document.createElement("iframe")
    iframe.setAttribute("src", `/dataset/code/tiktok/${window.dataset_id}/${window.row_number}/${column_id}`)
    iframe.style.width = "70vw"
    iframe.style.height = "100vh"
    document.getElementById(id).replaceChildren(iframe)
}

function display_image(id, column_id) {
    image = document.createElement("img")
    image.setAttribute("src", `/dataset/code/image/${window.dataset_id}/${window.row_number}/${column_id}.svg`)
    image.style.maxWidth = "70%";
    document.getElementById(id).replaceChildren(image)
}

function display_error(id, error_message) {
    span = document.createElement("pre");
    span.innerText = error_message;
    document.getElementById(id).replaceChildren(span);
}

function oembed(id, column_id){
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
    document.getElementById(id).replaceChildren();
    twttr.widgets.createTweet(
        url.split("/").at(-1),
        document.getElementById(id),
        {
            align: "center"
        }
    )
}

function initialise(dataset_id, columns, types) {
    document.getElementById("row-number").addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            if (event.target.value === "") return;
            event.preventDefault();
            go_to_row();
            event.target.value = "";
        }
    });
    window.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && event.ctrlKey) {
            event.preventDefault();
            submit();
            next_row();
        }
    });
    window.dataset_id = dataset_id;
    window.column_names = columns;
    window.column_types = types;
    window.columns = window.column_names.map(
        function(column_name, index) {
            return {
                name: column_name,
                type: window.column_types[index]
            };
        } 
    );
    next_row();
}
