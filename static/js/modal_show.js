
function modal_show_prapring(){
    $(document).ready(function(){
        $('#parserSettingUpModal').on('show.bs.modal', function(){
          
            var button = $('#tab_setup_button'),
                module = button.attr('data-bs-whatever'),
                modalTitle = $(this).find('.modal-title'),
                modal_nav_btn = $(this).find('#modal_navigate_button')

            if (module === "parser") {
                modalTitle.text(`Parser settings`)
                modal_nav_btn.addClass('visually-hidden')
            } else {
                modalTitle.text(`Exporter settings (1 of 2 steps)`)
                modal_nav_btn.removeClass('visually-hidden')
            }
        })
    })
}
