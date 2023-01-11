//load first utils script

function getStatus(selected_module, modal_stp_btn) { 
    const module = modal_stp_btn.attr('data-bs-whatever'),
          cookies = $('#cookieInput').val()
    
    return $.ajax({
        type: 'POST',
        url: '/settingup',
        data: {
            module: module,
            selected_module: selected_module,
            cookies: cookies
        }
    })
}

function show_spinners(modal_stp_btn) {
    const tab_stp_btn = $('#tab_setup_button')
          spinner = modal_stp_btn.children('.spinner-border')
                                 .removeClass('visually-hidden')
  
    tab_stp_btn.children('.spinner-border')
               .removeClass('visually-hidden')
    modal_stp_btn.text('')
                 .append(spinner)
}

function hide_setup_btn_spinner() {
    const spinner = $('#tab_setup_button .spinner-border')
    spinner.addClass('visually-hidden')
}

function show_state_on_btn(status, modal_stp_btn) {
    _ = hide_setup_btn_spinner()
  
    modal_stp_btn.removeClass('btn-outline-primary')
                 .addClass('text-capitalize')
  
    if (status === "fail"){
        modal_stp_btn.addClass('btn-danger')
    } else if (status === "done"){
        modal_stp_btn.addClass('btn-success')
    }
  
    modal_stp_btn.text(status)
}

function settingup_submit(){
    $(document).ready(async function(){
        const modal_menu = $('#moduleSettingUpModal'),
              modal_stp_btn = $('#modal_setup_button'),
              selected_module = $('#modulesSelect').val()

        _ = show_spinners(modal_stp_btn)
        modal_stp_btn.append('Waiting respond')
        modal_stp_btn.attr("disabled", "")
    
        var respond = {"status": 'fail'}
        try {
            respond = await getStatus(selected_module, modal_stp_btn)
        } catch(err) {}
      
        if ("msg" in respond) {
            show_responsed_alert(respond.msg)
        } else {
            show_remaded_alert('fail', 'Failed to send a request.')
        }
        _ = show_state_on_btn(respond['status'], modal_stp_btn)
        
        _ = await sleep(2000)
      
        modal_menu.modal('hide')
        location.reload()
    })
}