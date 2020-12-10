
var last_index_num = 10;
var tweets_per_page = 10;

$(function () {

    $('.load-area').on('click', function () {
        with_following = !!$(this).hasClass('with-following');
        id = $(this).attr('id').substr(10);
        $.post('/load_more', 'user_id=' + id + '&last_item_num=' + last_index_num + '&with_following=' + with_following)
            .done(function (data) {
                $(data.html).insertBefore('#load-area-' + id);
                last_index_num += tweets_per_page;

                if (data.fetched === 'False') {
                    $('.load-area').text('ツイートは以上です。').off();
                }
            })
    })
});