function get_title_data(clicked_item, case_data) {
    var titles, title_data
    const tab_id = clicked_item.closest('.tab-pane').attr('id'),
          title_id = clicked_item.attr('id')
  
    if (tab_id.includes("parse")) {
        titles = case_data['parse']
    } else if (tab_id.includes("export")) {
        titles = case_data['export']
    } else {
        return
    }
  
    for (const wlist in titles) {
        if (titles[wlist][title_id]) {
            title_data = titles[wlist][title_id]
            break
        }
    } 

    return title_data
}

function fill_offcanvas(clicked_item, title_data){
    var offcanvas_id = 'offcanvas_title_'
    const tab_id = clicked_item.closest('.tab-pane').attr('id')
  
    if (tab_id.includes("parse")) {
        offcanvas_id += 'left' 
    } else if (tab_id.includes("export")) {
        offcanvas_id += 'right' 
    } else {
        return
    }

    var target_offcanvas = $('#' + offcanvas_id),
        poster = target_offcanvas.find('#offcanvas_poster_val img'),
        name = target_offcanvas.find('#offcanvas_name_val'),
        original_name = target_offcanvas.find('#offcanvas_original_val'),
        other_names = target_offcanvas.find('#offcanvas_other_val'),
        genres = target_offcanvas.find('#offcanvas_genres_val'),
        type = target_offcanvas.find('#offcanvas_type_val'),
        year = target_offcanvas.find('#offcanvas_year_val'),
        episodes = target_offcanvas.find('#offcanvas_episodes_val'),
        status = target_offcanvas.find('#offcanvas_status_val'),
        visit_btn = target_offcanvas.find('#visit_btn')
  
    poster.attr('src', title_data['poster'])
    name.text(title_data['name'])
    original_name.text(title_data['original_name'])
    other_names.text(title_data['other_names'])
    genres.text(title_data['genres'])
    type.text(title_data['type'])
    year.text(title_data['year'])
    episodes.text(title_data['ep_count'])
    status.text(title_data['status'])
    visit_btn.attr('href', title_data['link'])
}