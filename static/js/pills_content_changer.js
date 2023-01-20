function _change_content(tab_data){
    var pill_tab = $('#pills-tab'),
        setup_button = pill_tab.find('#tab_setup_button'),
        action_button = pill_tab.find('#tab_action_button'),
        selected_module = pill_tab.find('#selected_module'),
        authorized_user = pill_tab.find('#authorized_user'),
        accord_block = $('#accordion_progress'),
        action_button_spinner = action_button.children('.spinner-border')
      
    pill_tab.attr("aria-labelledby", tab_data.tab_id)
    setup_button.attr("data-bs-whatever", tab_data.setup_btn_whatever)
  
    action_button.attr('name', tab_data.act_btn_val)
    action_button.val(tab_data.act_btn_val)
    action_button.text('')
    action_button.append(action_button_spinner)
    action_button.append(tab_data.act_btn_text)
  
    if (tab_data.auth_usr.length !== 0) {
        selected_module.val(tab_data.selected_mod)
        authorized_user.val(tab_data.auth_usr)
    }

    var target_accord = accord_block.find('#' + tab_data.target_accord)
    target_accord.removeClass('visually-hidden')
}

function _get_tab_data(tab_id, parser_data, exporter_data) {
    var tabs_data = {
        'pills-parser-tab': {
            'tab_id': "pills-parser-tab",
            'setup_btn_whatever': "parser",
            'act_btn_val': "parse",
            'act_btn_text': "Parse",
            'selected_mod': parser_data['selected_module'],
            'auth_usr': parser_data['username'],
            'target_accord': 'parse_accordion_item'
        },
        'pills-exporter-tab': {
            'tab_id': "pills-exporter-tab",
            'setup_btn_whatever': "exporter",
            'act_btn_val': "export",
            'act_btn_text': "Export",
            'selected_mod': exporter_data['selected_module'],
            'auth_usr': exporter_data['username'],
            'target_accord': 'export_accordion_item'
            
        }
    }
    return tabs_data[tab_id]
}

function _prepare_pill(selected_pill_id) {
    var pill_tab = $('#pills-tab'),
        selected_module = pill_tab.find('#selected_module'),
        authorized_user = pill_tab.find('#authorized_user'),
        other_accords = $('#accordion_progress .accordion-item:not(.visually-hidden)')

    selected_module.val('[Not selected]')
    authorized_user.val('[Not authorized]')
    other_accords.addClass('visually-hidden')
}

function _change_pill_content(selected_pill_id, parser_data, exporter_data) {
    _ = _prepare_pill(selected_pill_id)
    tab_data = _get_tab_data(selected_pill_id, parser_data, exporter_data)
    _ = _change_content(tab_data)
}

function pills_content_changer(parser_data, exporter_data){
    $(document).ready(function(){
        //initial filling
        var selected_pill_id = $('#pills-tabs .active').attr('id')
        _ = _change_pill_content(selected_pill_id, parser_data, exporter_data)
        
        $('#pills-tabs .nav-link').on(
            'click', 
            async function () {
                //change animation delay
                await sleep(100)
                                        
                selected_pill_id = $(this).attr('id')
                _ = _change_pill_content(selected_pill_id, parser_data, exporter_data)
        })
    })
}