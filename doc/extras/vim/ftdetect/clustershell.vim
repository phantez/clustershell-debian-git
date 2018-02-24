"
" Installed As: vim/ftdetect/clustershell.vim
" $Id: clustershell.vim 257 2010-05-19 21:27:39Z st-cea $
"
au BufNewFile,BufRead *clush.conf               setlocal filetype=clushconf
au BufNewFile,BufRead *groups.conf              setlocal filetype=groupsconf
