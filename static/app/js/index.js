function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        let cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            let cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

let csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});


function get_tweet_id(element) {
    return $(element).parents('.tweet-body').attr('id');
}

function show_alert(message) {

    $('.overlay').show();
    $('#alert-text').text(message);
}

function unescapeHtml(target) {
    if (typeof target !== 'string') return target;

    var patterns = {
        '&lt;': '<',
        '&gt;': '>',
        '&amp;': '&',
        '&quot;': '"',
        '&#x27;': '\'',
        '&#x60;': '`'
    };

    return target.replace(/&(lt|gt|amp|quot|#x27|#x60);/g, function (match) {
        return patterns[match];
    });
}

$(function () {
    // generate hashtag link
    const tweets = document.getElementsByClassName('tweet-content');
    for (let i = 0; i < tweets.length; i++) {
        tweets[i].innerHTML = tweets[i].innerHTML.replace(/(#[^ ]+)/, '<span class="hashtag">$1</span>');
    }


    $('.post-tweet').on('click', function () {
        const $form = $(this).parents('form');
        let tweet = $form.find('.tweet-content-form').html().trim();

        tweet = tweet.replace(/<\/?div>/g, '');
        tweet = unescapeHtml(tweet.replace(/<br>/g, '\n'));
        console.log(tweet);

        var input = document.createElement('input');
        input.setAttribute('type', 'hidden');
        input.setAttribute('name', 'tweet_content');
        input.setAttribute('value', tweet);
        $form.append(input);

        $form.submit();
    });


    const $textarea = $('.tweet-content-form');
    const $tweet_form = $('.tweet-form');

    $textarea.on('focus', function (e) {
        $tweet_form.removeClass('condensed');
        if ($(this).html().trim() === '<div><br></div>') {
            $(this).addClass('is-showPlaceholder');
        }

    }).on('blur', function (e) {
        if ($(this).html().trim() === '<div><br></div>') {
            $tweet_form.addClass('condensed');
            $(this).children('div').text('いまどうしてる？');
            $(this).removeClass('is-showPlaceholder');
        }
    }).on('paste', function (e) {
        e.preventDefault();
        var text = e.originalEvent.clipboardData.getData('text/plain');
        document.execCommand("insertHTML", false, text);
    }).on('keydown', function (e) {
        if (e.keyCode === 8 && $(this).html().trim() === '<div><br></div>') {
            // e.preventDefault();
        }
    });

    const text_max = 140; // 最大入力値
    $(".tweet-length").text(text_max - $(this).val().length);

    $textarea.on("keyup keydown keypress change paste", function (e) {
        if ($(this).html().trim() !== '<div><br></div>') {
            $(this).removeClass('is-showPlaceholder');
        } else {
            $(this).addClass('is-showPlaceholder');
        }

        let text_length = 0;
        const divs = $(this).children('div');
        for (let i = 0; i < divs.length; i++) {
            text_length += divs[i].textContent.length;
        }
        let countdown = text_max - text_length;
        $(this).parents('form').find(".tweet-length").text(countdown);

        if (countdown < 0) {
            $(this).parents('form').find(".tweet-length").css({
                color: '#ff0000',
                fontWeight: 'bold',
                display: 'inline'
            });
            $(this).parents('form').find(".post-tweet").prop('disabled', true);
        } else {
            $(this).parents('form').find(".tweet-length").css({
                color: '#000000',
                fontWeight: 'normal',
                display: 'none'
            });
            $(this).parents('form').find(".post-tweet").prop('disabled', false);
        }
    });


    $(".hashtag").on('click', function () {
        const tag = $(this).text().substr(1);
        console.log(tag);
        location.href = '/hashtag/?keyword=' + tag;

    });

    $(".no-auth").on('click', function () {
        location.href = '/';
    });

    $(".fa-comment.auth").on('click', function () {
        $(this).parent().siblings('.reply-form').toggle();
    });

    $(".fav.auth").on('click', function () {
        const id = get_tweet_id($(this));

        let url;
        if ($(this).hasClass('checked')) {
            url = '/unfav/'
        } else {
            url = '/fav/'
        }

        $.ajax({
            element: this,
            type: "POST",
            url: url + id,
        }).done(function (data) {
            if (data.status === 200) {
                $(this.element).toggleClass('fas far checked');
                let fav_count = data.count;
                if (fav_count === 0) {
                    fav_count = "";
                }
                $('.tweet-body#' + id).find('.fav-count').text(fav_count);
            }
        }).fail(function () {
            show_alert('何かがおかしいようです。')
        })
    });

    $(".rt.auth").on('click', function () {
        const id = get_tweet_id($(this));
        let url;
        if ($(this).hasClass('retweeted')) {
            url = '/unretweet/'
        } else {
            url = '/retweet/'
        }

        $.ajax({
            element: this,
            type: "POST",
            url: url + id,
        }).done(function (data) {
            if (data.status === 200) {
                $(this.element).toggleClass('retweeted');
                let rt_count = data.count;
                if (rt_count === 0) {
                    rt_count = "";
                }
                $('.tweet-body#' + id).find('.rt-count').text(rt_count);
            }
        }).fail(function () {
            show_alert('何かがおかしいようです。')
        })
    });


    $('#reply-modal').on('show.bs.modal', function (event) {
        const $button = $(event.relatedTarget);
        const tweetid = $button.data('tweetid');
        const username = $button.data('reply-to-username');
        const $modal = $('#reply-modal');
        $modal.find('.tweet-content-form').val("");
        $modal.find('.tweet-length').text("140");
        $.ajax({
            element: this,
            type: "POST",
            url: '/json/' + tweetid,
        }).done(function (data) {
            $modal.find('.username-header').text('返信先：' + username + 'さん');
            $modal.find('.username').attr('href', username).text(username);
            $modal.find('.time').text(data['time']);
            $modal.find('.tweet-content').text(data['content']);
            $modal.find('form').attr('action', '/reply/' + tweetid);
        }).fail(function () {
            $modal.find('.username-header').text('返信先：' + username + 'さん');
            $modal.find('.modal-body').hide();
            $modal.find('form').attr('action', '/reply/' + tweetid);
        })
    });

    $('#delete_modal').on('show.bs.modal', function (event) {
        const button = $(event.relatedTarget);
        const tweetid = button.data('tweetid');
        const modal = $(this);
        modal.find('#delete_button').attr('onclick', 'location.href="delete/' + tweetid + '"');
    });

    $('#delete_button').on('click', function () {
        $(this).prop('disabled', true);
    });

    $('#login_button').on('click', function () {
        const form_username = $('#username');
        const form_password = $('#password');
        const username = form_username.val();
        const password = form_password.val();
        $.post('/login', 'username=' + username + '&password=' + password)
            .done(function (data) {
                if (data.auth === 'success') {
                    location.href = '/'
                } else {
                    form_username.addClass('is-invalid');
                    form_password.addClass('is-invalid');
                    $('.error-msg').text('ユーザー名またはパスワードが異なります。');
                    $('.alert').show();
                }
            })
            .fail(function () {

            })
    });

    $('.follow-button').on('click', function () {
        const id = $(this).siblings('.user-id').text();

        let url;
        let text;
        if ($(this).hasClass('followed')) {
            url = '/unfollow/';
            text = 'フォローする';
        } else {
            url = '/follow/';
            text = 'フォロー解除';
        }

        $.ajax({
            element: this,
            type: "POST",
            url: url + id,
        }).done(function () {
            $(this.element).toggleClass('followed').text(text)
        })
    });

})
;