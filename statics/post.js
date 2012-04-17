
$('document').ready(function() {

    var in_chat = false;
    var joined = false;
    var token;
    var socket;

    //disable first
    $('#connect').attr('disabled', 'disabled');

    function onMessage(data)
    {
        msg = eval('('+data.data+')')

        if (msg.cmd == 'chat_ready')
        {
            in_chat = true;
            $('#connect').text('Connected');
        }
        else if (msg.cmd == 'chat_close')
        {
            joined = in_chat = false;
            $('#connect').text('Connect');

            $('#posts').append('<p style="text-align:right;color:red;border:solid 1px;">chat close!</p>')
        }
        else if (msg.cmd == 'chat_message')
        {
            $('#posts').append('<p style="text-align:left;border:solid 1px;">' + msg.msg + '</p>')
        }
    }

    function onOpened()
    {
        $('#connect').removeAttr('disabled');
    }

    function onClose()
    {
        alert('close!');
        $('#connect').attr('disabled', 'disabled');
    }

    function onError()
    {
        alert('error!');
        socket.close()
    }

    function gen_client_id()
    {
        function S4()
        {
            return (((Math.random()+1)*0x10000)|0).toString(16).substring(1);
        }
        return S4() + S4() + '-' + new Date().getTime().toString(32);
    }

    //generate unique id
    var clientid = gen_client_id();

    //create socket
    $.post('/cmd', {cmd:'connect', id: clientid}, function(data) {
        token = data.token;

        channel = new goog.appengine.Channel(token);
        socket = channel.open();
        socket.onopen = onOpened;
        socket.onmessage = onMessage;
        socket.onerror = onError;
        socket.onclose = onClose;
        
    }, 'json');

    $('#connect').click(function() {
        if (!in_chat && !joined)
        {
            joined = true;
            $('#connect').text('Waiting...');

            $.post('/cmd', {cmd:'join_chat', id: clientid});
        }
        else
        {
            $.post('/cmd', {cmd:'leave_chat', id: clientid});
        }
    });

    $('#send').click(function() {
        if (in_chat)
        {
            msg = $('#post').val();
            if (!msg)
            {
                return;
            }

            $('#send').attr('disabled', 'disabled');
            $.post('/cmd', {cmd:'chat_message', msg:msg, id:clientid}, function(data, code) {
                $('#post').val('');
                $('#posts').append('<p style="text-align:right;border:solid 1px;">' + msg + '</p>')

                $('#send').removeAttr('disabled');
            });
        }
    });
});
