const sleep = async (milliseconds) => {
    await new Promise(resolve => {
        return setTimeout(resolve, milliseconds)
    })
}

function capitalize_str(str){
    var res = str.substring(0, 1).toUpperCase() + str.substring(1)
    return res
}