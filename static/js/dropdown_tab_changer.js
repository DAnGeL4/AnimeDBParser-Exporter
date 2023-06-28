function switch_active_drpdwn_itm(clicked_itm) {           
    const dropdown_id = '#' + clicked_itm.closest('.btn-group').attr('id'),
          active_menu_items = $(dropdown_id + ' .dropdown-item.active'), 
          active_counters = $(dropdown_id + ' .dropdown-menu .badge'),
          clicked_itm_cntr = clicked_itm.parent()
                                        .find('span');
                               
    active_menu_items.removeClass('active');
    clicked_itm.addClass('active');
                               
    active_counters.removeClass('bg-light')
                   .addClass('bg-secondary');
    clicked_itm_cntr.removeClass('bg-secondary')
                    .addClass('bg-light');
  
    return {dropdown_id: dropdown_id,
            clicked_itm_cntr: clicked_itm_cntr};
};

function change_drpdwn_btn(clicked_itm, dropdown_id, clicked_itm_cntr) {
    var common_btn = $(dropdown_id + ' .dropdown-toggle'),
        common_counter = common_btn.children(),
        this_text = clicked_itm.clone()
                               .children()
                               .remove()
                               .end()
                               .text();
                               
    common_counter.html(clicked_itm_cntr.text().trim());
    common_btn.html("Watchlist: " + this_text + ' ')
              .append(common_counter);
};

function switch_titles_tab(clicked_itm) {
    var aria_controls = clicked_itm.attr('aria-controls'),
        target_tab = $('#' + aria_controls),
        tab_content_id = '#' + target_tab.parent().attr('id'),
        all_tabs = $(tab_content_id + ' .tab-pane');
                               
    all_tabs.hide()
            .removeClass('active show');
    target_tab.show()
              .addClass('active show');
};

$(document).ready(function(){
    $('.d-flex .flex-column').on('click', 
                                 '.dropdown-menu .dropdown-item', 
                                 function () {
        const clicked_itm = $(this);
                                   
        const {dropdown_id, clicked_itm_cntr} = switch_active_drpdwn_itm(clicked_itm);
        _ = change_drpdwn_btn(clicked_itm, dropdown_id, clicked_itm_cntr);
        _ = switch_titles_tab(clicked_itm);
    });
});