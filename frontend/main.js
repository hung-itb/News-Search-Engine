
appendTextHasGoogleLogoStyle($('#results-nav .sub-logo'), 'Soôgle')
$('#results-nav .sub-logo').click(() => window.location.href = '.')

function createDocElement(doc) {
    let [d, m, y] = doc['created_date'].split('/').map(x => Number(x))
    let distance = dateDiffInDays(new Date(y, m - 1, d), new Date())
    let dateMap = {
        0: 'Hôm nay',
        1: 'Hôm qua'
    }
    let html = `<div class="doc">
        <div class="doc-header">
            <img src="./resources/vnexpress.png" alt="" class="">
            <div class="info">
                <div class="provider">VnExpress</div>
                <div class="category">${(doc['category'] || '').replaceAll('_', ' ')}</div>
            </div>
        </div>

        <a class="doc-title" target="_blank" href="${doc['url']}">
            ${doc['title_original']}
        </a>

        <div class="doc-abstract">
            ${doc['abstract_original']}
        </div>

        <div class="created-date">
            ${dateMap[distance] || doc['created_date']}
        </div>
    </div>`

    return $(html)
}

let state = {
    q: '',
    category: '',
    page: 0,
    numDocsPerPage: 0
}

function success(res, resHeader, result) {
    let numFound = res.numFound
    if (numFound == 0) {
        $('#results .list-docs').append(
            $(`<div class="alert alert-warning">
                Không tìm thấy tin tức phù hợp!
            </div>`).css({
                'margin-top': '32px'
            })
        )
        return
    }
    let docs = res.docs
    state.numDocsPerPage = Math.max(docs.length, state.numDocsPerPage)
    for (let doc of docs) $('#results .list-docs').append(createDocElement(doc))

    if ($('#results .list-tags .tag').length == 0) {
        let facet_fields_result = result.facet_counts.facet_fields.category
        let categories = ['Tất cả']
        let category_counts = {'Tất cả': 0}
        for (let i = 0; i < facet_fields_result.length; i++) {
            if (i%2 == 0) {
                categories.push(facet_fields_result[i])
            } else {
                category_counts[categories[categories.length - 1]] = facet_fields_result[i]
                category_counts['Tất cả'] += facet_fields_result[i]
            }
        }
        categories = categories.filter(c => category_counts[c] != 0)
        categories.sort((c1, c2) => category_counts[c2] - category_counts[c1])
        for (let tag of categories) {
            let $tag = $(`<div class="tag">${tag.replaceAll('_', ' ')} (${category_counts[tag]})</div>`)
            $('#results .list-tags').append($tag)
            if (tag == 'Tất cả') {
                $tag.addClass('active')
            }
            $tag.click(() => {
                $('#results .list-tags .tag').removeClass('active')
                $('#results .page-control').html('')
                $tag.addClass('active')
                $('#results .list-docs').html('')
                doQuery(state.q, tag == 'Tất cả' ? null : tag)
            })
        }
    }

    $('#results .page-control').html('')
    let maxPage = Math.ceil((numFound || 1)/state.numDocsPerPage)
    let currPage = state.page
    let pageControlCandidates = [1, 2, 3, currPage, currPage + 1, currPage + 2, currPage + 3]
    pageControlCandidates = pageControlCandidates.filter(x => x >= 1 && x <= maxPage)
    pageControlCandidates = [...new Set(pageControlCandidates)]
    pageControlCandidates.sort((a, b) => a - b)
    let pageControlElems = []
    pageControlCandidates.forEach((v, i) => {
        if (i == 0) {
            pageControlElems.push(v)
            return
        }
        let prev = pageControlCandidates[i - 1]
        if (prev + 1 == v) {
            pageControlElems.push(prev + 1)
            return
        }
        if (prev + 2 == v) {
            pageControlElems.push(prev + 1)
            pageControlElems.push(v)
            return
        }
        pageControlElems.push('...')
        pageControlElems.push(v)
    })
    let last = pageControlElems[pageControlElems.length - 1]
    if (last + 1 == maxPage) {
        pageControlElems.push(maxPage)
    } else if (last != maxPage) {
        pageControlElems.push('...')
    }
    pageControlElems.forEach(e => {
        let $e = null
        if (e == '...') {
            $e = $('<div class="vv">...</div>')
        } else {
            $e = $(`<div class="e">${e}</div>`)
            if (e == currPage + 1) $e.addClass('active')
            else {
                $e.click(() => {
                    $('#results .list-docs').html('')
                    $('#results .page-control .e').removeClass('active')
                    $e.addClass('active')
                    doQuery(state.q, state.category, e - 1)
                })
            }
        }
        $('#results .page-control').append($e)
    })
}

function doQuery(q, category = null, page = 0) {
    let data = {
        q, category, page
    }
    Object.assign(state, data)
    $.ajax({
        type: 'GET',
        url: window.FRONTEND_API_URL + '/api/search',
        contentType: "application/json",
        dataType: 'json',
        data: data,
        success: (result, status, xhr) => success(result.response, result.responseHeader, result),
        error: (xhr, status, error) => {
            $('#results .list-docs').append(
                $(`<div class="alert alert-danger">
                    Không thể kết nối tới server!
                </div>`).css({
                    'margin-top': '32px'
                })
            )
        },
        complete: () => $('#loader').remove()
    })
}

$('#results-nav .search-input').on('keydown', function (e) {
    if (e.keyCode == 13) { // Enter
        let q = $(this).val()
        if (q == '') return
        window.location.href = './search.html?q=' + q
    }
})

let query = new URLSearchParams(window.location.search).get('q')
$('#results .list-docs').html('')
$('#results .list-tags').html('')
doQuery(query)
$('#results-nav .search-input').val(query)
