#!/usr/bin/env bash
# packaging/build-deb.sh
# Builds arfix-termux.deb and arfix-debian.deb from the repo source.
# Usage: bash packaging/build-deb.sh
#
# Requires: dpkg-deb (part of dpkg on Debian/Ubuntu; install via
# `apt install dpkg-dev` if missing. Can be run on any Linux system
# with dpkg-deb available, even to build the Termux variant.)

set -e
cd "$(dirname "$0")/.."   # repo root

REPO_ROOT="$(pwd)"
BUILD_DIR="$(mktemp -d)"

build_variant() {
    local variant="$1"          # "termux" or "debian"
    local src_dst="$2"          # path (relative to package root) where source lands
    local out_name="arfix-${variant}.deb"

    local pkg_root="$BUILD_DIR/$variant"
    mkdir -p "$pkg_root/DEBIAN"
    mkdir -p "$pkg_root/$src_dst"

    cp -r "$REPO_ROOT/arfix" "$pkg_root/$src_dst/"
    rm -rf "$pkg_root/$src_dst/arfix/__pycache__"
    cp "$REPO_ROOT/pyproject.toml" "$pkg_root/$src_dst/"
    cp "$REPO_ROOT/README.md" "$pkg_root/$src_dst/"
    cp "$REPO_ROOT/scripts/arfix-shell-hook.sh" "$pkg_root/$src_dst/"

    cp "$REPO_ROOT/packaging/deb-$variant/DEBIAN/control" "$pkg_root/DEBIAN/"
    cp "$REPO_ROOT/packaging/deb-$variant/DEBIAN/postinst" "$pkg_root/DEBIAN/"
    cp "$REPO_ROOT/packaging/deb-$variant/DEBIAN/prerm" "$pkg_root/DEBIAN/"
    chmod 755 "$pkg_root/DEBIAN/postinst" "$pkg_root/DEBIAN/prerm"
    find "$pkg_root" -type d -exec chmod 755 {} \;

    dpkg-deb --build --root-owner-group "$pkg_root" "$REPO_ROOT/$out_name"
    echo "==> built $out_name"
}

build_variant "termux" "data/data/com.termux/files/usr/share/arfix-src"
build_variant "debian" "usr/share/arfix-src"

rm -rf "$BUILD_DIR"
echo "==> done: arfix-termux.deb, arfix-debian.deb"
