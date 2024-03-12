
function appendTextHasGoogleLogoStyle(container, textOrTextArray) {
    if (!container) return

    let texts = Array.isArray(textOrTextArray) ? textOrTextArray : [textOrTextArray]

    texts.forEach(text => {
        let colors = ['b', 'r', 'y', 'b', 'g', 'r']
        let countLetters = text.replaceAll(' ', '').length
        let groupLength = Math.floor(countLetters / colors.length)
    
        let groupLengths = colors.map(_ => groupLength)
    
        let redundant = countLetters - groupLength * colors.length
        let x = Math.floor((countLetters - groupLength * colors.length) / 2) + 1
        for (let i = x; i < x + redundant; i++) {
            groupLengths[i]++
        }
    
        let countCurrentColor = 0
        let currentColorIndex = 0
        let html = ''
    
        for (let i = 0; i < text.length; i++) {
            if (text[i] == ' ') {
                html += ' '
                continue
            }
            html += `<span class="fake_google_text ${colors[currentColorIndex]}">${text[i]}</span>`
    
            countCurrentColor++
            if (countCurrentColor == groupLengths[currentColorIndex]) {
                countCurrentColor = 0
                if (currentColorIndex != colors.length - 1) {
                    currentColorIndex += 1
                }
            }
        }
        $(container).append(html)
    })
    
    return $(container)
}

function dateDiffInDays(a, b) {
    const _MS_PER_DAY = 1000 * 60 * 60 * 24;
    const utc1 = Date.UTC(a.getFullYear(), a.getMonth(), a.getDate());
    const utc2 = Date.UTC(b.getFullYear(), b.getMonth(), b.getDate());
  
    return Math.floor((utc2 - utc1) / _MS_PER_DAY);
}
