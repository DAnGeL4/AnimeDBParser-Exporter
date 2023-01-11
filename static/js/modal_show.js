function fill_modal_slct(modules_options) {
    var select = $('#modulesSelect').empty()
    for (var i = 0; i < modules_options.length; i++){
        var option = new Option(modules_options[i], modules_options[i])
        select.append(option)
    }
    return select
}

function fill_modal(module_data) {
    var select = fill_modal_slct(module_data.options), 
        modal_setup_button = $('#modal_setup_button'),
        cookie_input = $('#cookieInput')
  
    select.val(module_data.data.selected_module)
    modal_setup_button.attr( "data-bs-whatever", module_data.key )
    cookie_input.val(module_data.data.cookies)
}

function modal_show_prapring(parse_modules, export_modules, 
                             parser_data, exporter_data){
    $(document).ready(function(){
        $('#moduleSettingUpModal').on('show.bs.modal', function(){
            const modules_data = {
                      'parser': {
                          key: 'parser',
                          options: parse_modules,
                          data: parser_data
                      },
                      'exporter': {
                          key: 'exporter',
                          options: export_modules,
                          data: exporter_data
                      }
                  }
          
            var button = $('#tab_setup_button'),
                module = button.attr('data-bs-whatever'),
                modalTitle = $(this).find('.modal-title')
          
            modalTitle.text(`Settings (${module})`)
            _ = fill_modal(modules_data[module])
        })
    })
}
