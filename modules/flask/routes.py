#--Start imports block
#System imports

#Custom imports
#--Finish imports block

#--Start global constants block
name_id = '/<int:name_id>'

routes = dict({
    "index": '/',
    "slct_rm_gen": '/slct_rm_gen',
    "exclude": '/exclude_name' + name_id,
    "action": '/action',
    "settingup": '/settingup',
})
#--Finish global constants block