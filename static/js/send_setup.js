//load first utils script

function getStatus(selected_module, modal_stp_btn, cookies) { 
    const module = modal_stp_btn.attr('data-bs-whatever');
    
    return $.ajax({
        type: 'POST',
        url: '/settingup',
        data: {
            module: module,
            selected_module: selected_module,
            cookies: cookies
        }
    });
};

function _show_spinners(modal_stp_btn) {
    const tab_stp_btn = $('#tab_setup_button'),
          spinner = modal_stp_btn.children('.spinner-border')
                                 .removeClass('visually-hidden');
  
    tab_stp_btn.children('.spinner-border')
               .removeClass('visually-hidden');
    modal_stp_btn.text('')
                 .append(spinner);
};

function _hide_setup_btn_spinner() {
    const spinner = $('#tab_setup_button .spinner-border');
    spinner.addClass('visually-hidden');
};

function _hide_modal_btn_spinner(modal_stp_btn) {
    const spinner = modal_stp_btn.children('.spinner-border')
                                 .addClass('visually-hidden');
};

function _show_state_on_btn(status, modal_stp_btn) {
    _ = _hide_setup_btn_spinner();
    _ = _hide_modal_btn_spinner(modal_stp_btn);
  
    modal_stp_btn.removeClass('btn-outline-primary')
                 .addClass('text-capitalize');
  
    if (status === "fail"){
        modal_stp_btn.addClass('btn-danger');
    } else if (status === "done"){
        modal_stp_btn.addClass('btn-success');
    };
  
    const spinner = modal_stp_btn.children('.spinner-border');
    modal_stp_btn.text('')
                 .append(spinner)
                 .append(status);
};

function _set_btn_to_default(modal_stp_btn) {
    const spinner = modal_stp_btn.children('.spinner-border');
    
    modal_stp_btn.removeClass('btn-danger')
                 .removeClass('btn-success')
                 .addClass('btn-outline-primary')
                 .text('')
                 .append(spinner)
                 .append('Login and get user data')
                 .removeAttr("disabled");
};

function _show_status(respond, modal_stp_btn) {
    if ("msg" in respond) {
        show_responsed_alert(respond.msg);
    } else {
        show_remaded_alert('fail', 'Failed to send a request.');
    }
    
    _ = _show_state_on_btn(respond.status, modal_stp_btn);
};

function _finish_setup(respond, modal_menu, modal_stp_btn) {
    const action = $('#tab_action_button').attr('value'),
          module = modal_stp_btn.attr('data-bs-whatever');

    if (respond.status == 'fail' || !module.includes(action)) {
        _ = _set_btn_to_default(modal_stp_btn);
    } else {
        modal_menu.modal('hide');
        location.reload();
    };
};

function settingup_submit(caller){
    $(document).ready(async function(){
        const modal_menu = caller.parents('.modal.fade').first(),
              modal_stp_btn = modal_menu.find('#modal_setup_button').first(),
              cookies = modal_menu.find('#cookieInput').first().val(),
              selected_module = modal_menu.find('#modulesSelect').first().val();

        _ = _show_spinners(modal_stp_btn);
        modal_stp_btn.append('Waiting respond');
        modal_stp_btn.attr("disabled", "");
    
        var respond = {"status": 'fail'};
        try {
            respond = await getStatus(selected_module, modal_stp_btn, cookies);
        } catch(err) {};
      
        _ = _show_status(respond, modal_stp_btn);
        _ = await sleep(2000);
        _ = _finish_setup(respond, modal_menu, modal_stp_btn);
    });
};