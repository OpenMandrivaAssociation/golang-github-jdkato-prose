# If any of the following macros should be set otherwise,
# you can wrap any of them with the following conditions:
# - %%if 0%%{centos} == 7
# - %%if 0%%{?rhel} == 7
# - %%if 0%%{?fedora} == 23
# Or just test for particular distribution:
# - %%if 0%%{centos}
# - %%if 0%%{?rhel}
# - %%if 0%%{?fedora}
#
# Be aware, on centos, both %%rhel and %%centos are set. If you want to test
# rhel specific macros, you can use %%if 0%%{?rhel} && 0%%{?centos} == 0 condition.
# (Don't forget to replace double percentage symbol with single one in order to apply a condition)

# Generate devel rpm
%global with_devel 1
# Build project from bundled dependencies
%global with_bundled 0
# Build with debug info rpm
%global with_debug 1
# Run tests in check section
%global with_check 1
# Generate unit-test rpm
%global with_unit_test 1

%if 0%{?with_debug}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package   %{nil}
%endif

%if ! 0%{?gobuild:1}
%define gobuild(o:) go build -ldflags "${LDFLAGS:-} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n')" -a -v -x %{?**};
%endif

%global provider        github
%global provider_tld    com
%global project         jdkato
%global repo            prose
# https://github.com/jdkato/prose
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path     %{provider_prefix}
%global commit          2f94c80e59645786cd98cdcda1263e5ae903f6fd
%global shortcommit     %(c=%{commit}; echo ${c:0:7})
%global commitdate      20170911

Name:           golang-%{provider}-%{project}-%{repo}
Version:        0
Release:        0.6.%{commitdate}git%{shortcommit}%{?dist}
Summary:        Golang library for text processing
License:        MIT
URL:            https://%{provider_prefix}
Source0:        https://%{provider_prefix}/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz

# e.g. el6 has ppc64 arch without gcc-go, so EA tag is required
ExclusiveArch:  %{?go_arches:%{go_arches}}%{!?go_arches:%{ix86} x86_64 aarch64 %{arm}}
# If go_compiler is not set to 1, there is no virtual provide. Use golang instead.
BuildRequires:  %{?go_compiler:compiler(go-compiler)}%{!?go_compiler:golang}
# Provide main package name
Provides: prose%{?_isa} = %{version}-%{release}

%if ! 0%{?with_bundled}
# cmd/prose/main.go
BuildRequires: golang(github.com/urfave/cli)

# Remaining dependencies not included in main packages
BuildRequires: golang(github.com/montanaflynn/stats)
BuildRequires: golang(github.com/shogo82148/go-shuffle)
BuildRequires: golang(github.com/neurosnap/sentences)
%endif

%description
%{summary}

%if 0%{?with_devel}
%package devel
Summary:       %{summary}
BuildArch:     noarch

%if 0%{?with_check} && ! 0%{?with_bundled}
BuildRequires: golang(github.com/montanaflynn/stats)
BuildRequires: golang(github.com/shogo82148/go-shuffle)
BuildRequires: golang(github.com/neurosnap/sentences)
%endif

Requires:      golang(github.com/montanaflynn/stats)
Requires:      golang(github.com/shogo82148/go-shuffle)
Requires:      golang(github.com/neurosnap/sentences)

Provides:      golang(%{import_path}) = %{version}-%{release}
Provides:      golang(%{import_path}/chunk) = %{version}-%{release}
Provides:      golang(%{import_path}/summarize) = %{version}-%{release}
Provides:      golang(%{import_path}/tag) = %{version}-%{release}
Provides:      golang(%{import_path}/tokenize) = %{version}-%{release}
Provides:      golang(%{import_path}/transform) = %{version}-%{release}

%description devel
%{summary}

This package contains library source intended for
building other packages which use import path with
%{import_path} prefix.
%endif

%if 0%{?with_unit_test} && 0%{?with_devel}
%package unit-test-devel
Summary:         Unit tests for %{name} package
%if 0%{?with_check}
#Here comes all BuildRequires: PACKAGE the unit tests
#in %%check section need for running
%endif

# test subpackage tests code from devel subpackage
Requires:        %{name}-devel = %{version}-%{release}

%if 0%{?with_check} && ! 0%{?with_bundled}
BuildRequires: golang(github.com/jdkato/syllables)
BuildRequires: golang(github.com/stretchr/testify/assert)
%endif

Requires:      golang(github.com/jdkato/syllables)
Requires:      golang(github.com/stretchr/testify/assert)

%description unit-test-devel
%{summary}

This package contains unit tests for project
providing packages with %{import_path} prefix.
%endif

%prep
%setup -q -n %{repo}-%{commit}

%build
mkdir -p src/%{provider}.%{provider_tld}/%{project}
ln -s ../../../ src/%{import_path}

%if ! 0%{?with_bundled}
export GOPATH=$(pwd):%{gopath}
%else
# No dependency directories so far
export GOPATH=$(pwd):%{gopath}
%endif

%gobuild -o bin/cmd/prose %{import_path}/cmd/prose

%install
install -d -p %{buildroot}%{_bindir}
install -p -m 0755 bin/cmd/prose %{buildroot}%{_bindir}

# source codes for building projects
%if 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
echo "%%dir %%{gopath}/src/%%{import_path}/." >> devel.file-list
# find all *.go but no *_test.go files and generate devel.file-list
for file in $(find . \( -iname "*.go" -or -iname "*.s" \) \! -iname "*_test.go") ; do
    dirprefix=$(dirname $file)
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$dirprefix
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> devel.file-list

    while [ "$dirprefix" != "." ]; do
        echo "%%dir %%{gopath}/src/%%{import_path}/$dirprefix" >> devel.file-list
        dirprefix=$(dirname $dirprefix)
    done
done
%endif

# testing files for this project
%if 0%{?with_unit_test} && 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
# find all *_test.go files and generate unit-test-devel.file-list
for file in $(find . -iname "*_test.go") ; do
    dirprefix=$(dirname $file)
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$dirprefix
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> unit-test-devel.file-list

    while [ "$dirprefix" != "." ]; do
        echo "%%dir %%{gopath}/src/%%{import_path}/$dirprefix" >> devel.file-list
        dirprefix=$(dirname $dirprefix)
    done
done
# install data used for tests
cp -rpav ./testdata %{buildroot}/%{gopath}/src/%{import_path}/
echo "%%{gopath}/src/%%{import_path}/testdata" >> unit-test-devel.file-list
%endif

%if 0%{?with_devel}
sort -u -o devel.file-list devel.file-list
%endif

%check
%if 0%{?with_check} && 0%{?with_unit_test} && 0%{?with_devel}
%if ! 0%{?with_bundled}
export GOPATH=%{buildroot}/%{gopath}:%{gopath}
%else
# No dependency directories so far

export GOPATH=%{buildroot}/%{gopath}:%{gopath}
%endif

%if ! 0%{?gotest:1}
%global gotest go test
%endif

%gotest %{import_path}/chunk
%gotest %{import_path}/summarize
%gotest %{import_path}/tag
%gotest %{import_path}/tokenize
%gotest %{import_path}/transform
%endif

#define license tag if not already defined
%{!?_licensedir:%global license %doc}

%files
%license LICENSE
%doc AUTHORS.md README.md
%{_bindir}/prose

%if 0%{?with_devel}
%files devel -f devel.file-list
%license LICENSE
%doc AUTHORS.md README.md
%dir %{gopath}/src/%{provider}.%{provider_tld}/%{project}
%endif

%if 0%{?with_unit_test} && 0%{?with_devel}
%files unit-test-devel -f unit-test-devel.file-list
%license LICENSE
%doc AUTHORS.md README.md
%endif

%changelog
* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0-0.6.20170911git2f94c80
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Mon Sep 11 2017 Athos Ribeiro <athoscr@fedoraproject.org> - 0-0.5.20170911git2f94c80
- Update revision
- Remove line changing test data files permissions

* Mon Sep 11 2017 Athos Ribeiro <athoscr@fedoraproject.org> - 0-0.4.20170806gita678fc7
- Remove Executable flag from test data files
- Fix binary file path in %%files section

* Fri Sep 08 2017 Athos Ribeiro <athoscr@fedoraproject.org> - 0-0.3.20170806gita678fc7
- Remove patch for gopkg.in dependencies. neurosnap/sentences ships both namespaces

* Fri Aug 18 2017 Athos Ribeiro <athoscr@fedoraproject.org> - 0-0.2.20170806gita678fc7
- Add missing neurosnap/sentences dependency
- Patch sources to depend on github neurosnap/sentences instead of gopkg.in releases

* Fri Aug 11 2017 Athos Ribeiro <athoscr@fedoraproject.org> - 0-0.1.20170806gita678fc7
- First package for Fedora

