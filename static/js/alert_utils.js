$(document).ready(function(){
    $('#alert_block').on('click', '.btn-close', function () {
        $('#alert_block').find('.alert')
                         .addClass('visually-hidden')
    })
})

function show_alert() {
    $('#alert_block').find('.alert')
                     .removeClass('visually-hidden')
}

function change_alert(rendered_template) {
    $('#alert_block').html(rendered_template)
}

function remade_alert(status, message) {
    var alert = $('#alert_block').find('.alert'), 
        status_colors = {'done': 'alert-success', 'info': 'alert-primary', 
                        'fail': 'alert-danger', 'warning': 'alert-warning'}
    
    alert.removeClass(status_colors.info)
         .addClass(status_colors[status])
    alert.find('strong')
         .text(status)
         .end()
         .find('span')
         .text(message)
}

function show_responsed_alert(rendered_template) {
    change_alert(rendered_template)
    show_alert()
}

function show_remaded_alert(status, message) {
    remade_alert(status, message)
    show_alert()
}