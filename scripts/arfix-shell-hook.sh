# ==== arfix auto-wrap (added automatically by install.sh) ====
# Wraps common text-printing commands and fixes any Arabic in their
# output automatically, without needing to type arfix or smartcat.
#
# Note: this does NOT cover interactive full-screen programs like
# vim/nano/top/htop — they don't "print lines" so they're unaffected
# (and shouldn't be).

_arfix_wrap() {
    command "$1" "${@:2}" | arfix
}

cat()  { _arfix_wrap cat  "$@"; }
echo() { command echo "$@" | arfix; }
grep() { _arfix_wrap grep "$@"; }
head() { _arfix_wrap head "$@"; }
tail() { _arfix_wrap tail "$@"; }
# ==== end arfix auto-wrap ====
