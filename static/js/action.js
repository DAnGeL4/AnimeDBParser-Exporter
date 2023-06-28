function send_action(action, cmd, progress_xpnd = false){
    var optional_args = {
        selected_tab: arguments[3] ? arguments[3] : null,
        progress_xpnd: progress_xpnd
    };
  
    return $.ajax({
        type: 'POST',
        url: '/action',
        data:{
            action: action,
            cmd: cmd,
            optional_args: JSON.stringify(optional_args)
        }
    });
};

function fill_statusbar(action, statusbar_tmpl) {
    const accord = $('#accordion_progress'),
          accord_itm_id = action + '_accordion_item';
  
    accord.children('#' + accord_itm_id)
          .remove()
          .end()
          .append(statusbar_tmpl);
};

function get_action_deferred_worker(){
    var worker = $.Deferred();
  
    worker.done(function(action, titles_blk_id, response) {
        _ = show_responsed_alert(response.msg);
        _ = fill_statusbar(action, response.statusbar_tmpl);
        _ = hide_act_btn_spinner();
        _ = change_action_btn("stop");
        $(titles_blk_id).html(response.title_tmpl);
    });
  
    worker.fail(function(action, titles_blk_id, response) {
        _ = show_responsed_alert(response.msg);
        _ = fill_statusbar(action, response.statusbar_tmpl);
        _ = hide_act_btn_spinner();
        _ = change_action_btn("stop");
    });
  
    worker.progress(function(action, titles_blk_id, response) {
        _ = fill_statusbar(action, response.statusbar_tmpl);
        $(titles_blk_id).html(response.title_tmpl);
    });
    
    return worker
};

function get_selected_tab(drpdwn_menu_id) {
    var selected_tab = $(drpdwn_menu_id + ' .dropdown-menu .active');
    selected_tab = selected_tab.children()
                               .remove()
                               .end()
                               .text()
                               .trim();
    return selected_tab
};

function get_statusbar_state(action) {
    const accord_id = action + '_accordion_collapse';
    return $('#' + accord_id).hasClass("show");
};

function get_deferred_timer(action, interval, 
                            titles_blk_id, drpdwn_menu_id) {
    var worker = get_action_deferred_worker();
      
    var timer = setInterval(async () => {
        const progress_xpnd = get_statusbar_state(action),
              selected_tab = get_selected_tab(drpdwn_menu_id);
      
        const response = await send_action(action, 
                                         "ask", 
                                         progress_xpnd, 
                                         selected_tab);
      
        if (response.status === "done") {
            clearInterval(timer);
            worker.resolve(action, titles_blk_id, response);
          
        } else if (response.status === "processed") {
            worker.notify(action, titles_blk_id, response);
          
        } else {
            clearInterval(timer);
            worker.reject(action, titles_blk_id, response);
        };
      
    }, interval);
  
};

function data_updatind_job(action, interval){
    var titles_blk_id, drpdwn_menu_id;
  
    if (action === 'parse') {
        titles_blk_id = '#parsed_titles';
        drpdwn_menu_id = '#parsed_dropdown_menu';
      
    } else if (action === 'export') {
        titles_blk_id = '#exported_titles';
        drpdwn_menu_id = '#exported_dropdown_menu';
    }
  
    var timer = get_deferred_timer(action, interval, 
                                   titles_blk_id, drpdwn_menu_id);
};

function check_authorization(username){
    if (username) {
        return true;
    } else {
        _ = show_remaded_alert('fail', 'User not authorized.');
        return false;
    };
};

function is_fail(response) {
    if ((!response) || 
          (!('status' in response))) {
        _ = show_remaded_alert('fail', 'Fail.');
        return true;
    } else if (response.status === 'fail') {
        if ("msg" in response) {
            _ = show_responsed_alert(response.msg);
        } else {
            _ = show_remaded_alert('fail', 'Fail.');
        };
        return true;
    };
    return false;
};

function change_action_btn(key) {
    var setup_btn = $('#tab_setup_button'),
        action_btn = $('#tab_action_button'),
        action = action_btn.val(),
        inactive_pills = $('#pills-tabs button:not(.active)'),
        spinner = action_btn.children('.spinner-border');

    if (key === "stop") {
        inactive_pills.removeClass('disabled');
        setup_btn.removeAttr("disabled");
        action_btn.prop("name", action);
        action_btn.text('');
        action_btn.append(spinner);
        action_btn.append(capitalize_str(action));
      
    } else if (key === "do") {
        inactive_pills.addClass('disabled');
        setup_btn.prop("disabled", true);
        action_btn.prop("name", "stop");
        action_btn.text('');
        action_btn.append(spinner);
        action_btn.append('Stop');
    };
};

function show_act_btn_spinner() {
    const spinner = $('#tab_action_button .spinner-border');
    spinner.removeClass('visually-hidden');
};

function hide_act_btn_spinner() {
    const spinner = $('#tab_action_button .spinner-border');
    spinner.addClass('visually-hidden');
};

function do_action(username){
    $(document).ready(async function(){
        var action_btn = $('#tab_action_button'),
            action_btn_name = action_btn.attr("name"),
            action = action_btn.val(),
            progress_xpnd = get_statusbar_state(action),
            interval = 3 * 1000;

        if (action_btn_name === "stop") {
            const response = await send_action(action, "stop", progress_xpnd);
            if (is_fail(response)) { return; };

            _ = hide_act_btn_spinner();
            _ = show_responsed_alert(response.msg);
            if (response.statusbar_tmpl) {
                _ = fill_statusbar(action, response.statusbar_tmpl);
            };
          
            _ = change_action_btn("stop");
          
        } else {
            if (!check_authorization(username)) { return; };
          
            const response = await send_action(action, "start", progress_xpnd);
            if (is_fail(response)) { return; };
          
            _ = show_act_btn_spinner();
            _ = show_responsed_alert(response.msg);
            if (response.statusbar_tmpl) {
                _ = fill_statusbar(action, response.statusbar_tmpl);
            };
          
            _ = change_action_btn("do");
            _ = data_updatind_job(action, interval);
        };
    });
};