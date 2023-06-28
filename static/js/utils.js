const sleep = async (milliseconds) => {
    await new Promise(resolve => {
        return setTimeout(resolve, milliseconds);
    });
};

function capitalize_str(str){
    var res = str.substring(0, 1).toUpperCase() + str.substring(1);
    return res;
};

function send_state(){
    //get_selected_tab from action.js which is loaded after
    //so calling send_state after loading action.js
    $(window).on('beforeunload', function(event) {
        var selected_pill_id = $('#pills-tabs .active').attr('id'),
            parsed_drpdwn_id = '#parsed_dropdown_menu',
            exported_drpdwn_id = '#exported_dropdown_menu';
            
        _ = $.ajax({
            type: 'POST',
            async: false,
            url: '/data_rcv',
            data: {
                selected_pill_id: selected_pill_id,
                selected_parsed_tab: get_selected_tab(parsed_drpdwn_id),        //!
                selected_exported_tab: get_selected_tab(exported_drpdwn_id)     //!
            }
        });
    });
};