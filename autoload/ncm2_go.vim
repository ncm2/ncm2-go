if get(s:, 'loaded', 0)
    finish
endif
let s:loaded = 1

let g:ncm2_go#proc = yarp#py3('ncm2_go')

let g:ncm2_go#source = extend(
            \ get(g:, 'ncm2_go#source', {}), {
            \ 'name': 'go',
            \ 'priority': 9,
            \ 'mark': 'go',
            \ 'early_cache': 1,
            \ 'subscope_enable': 1,
            \ 'scope': ['go'],
            \ 'word_pattern': '[\w/]+',
            \ 'complete_pattern': ['\.', '::'],
            \ 'on_complete': 'ncm2_go#on_complete',
            \ 'on_warmup': 'ncm2_go#on_warmup',
            \ }, 'keep')

let g:ncm2_go#gocode_path = get(g:, 'ncm2_go#gocode_path', 'gocode')

func! ncm2_go#init()
    call ncm2#register_source(g:ncm2_go#source)
endfunc

func! ncm2_go#on_warmup(ctx)
    call g:ncm2_go#proc.jobstart()
endfunc

func! ncm2_go#on_complete(ctx)
    call g:ncm2_go#proc.try_notify('on_complete',
            \ a:ctx,
            \ ncm2_go#data(),
            \ getline(1, '$'))
endfunc

func! ncm2_go#error(msg)
    call g:ncm2_go#proc.error(a:msg)
endfunc

func! ncm2_go#data()
    return {
                \ 'gocode_path': g:ncm2_go#gocode_path
                \ }
endfunc
