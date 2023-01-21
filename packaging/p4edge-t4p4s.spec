%{!?t4p4sroot: %global t4p4sroot /root/t4p4s}
%{!?grpcroot: %global grpcroot /root/grpc}
%{!?piroot: %global piroot /root/PI}
%{!?p4rtroot: %global p4rtroot /root/P4Runtime_GRPCPP}
%{!?shortname: %global shortname t4p4s}

Name:           p4edge-t4p4s
Version:        0.0.0
Release:        0%{?dist}
Summary:        P4Edge t4p4s
License:        Apache 2.0
URL:            https://github.com/p4edge/t4p4s
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3, python3-pip, ccache, lsof, netcat, ninja-build, libdpdk-dev
BuildRequires:  debbuild-macros-systemd, git
Packager:       Dávid Kis <kidraai@.inf.elte.hu>

%description
P4Edge t4p4s

%prep
%autosetup
cp ./packaging/find_system_p4test.patch ./src/hlir16/
cd ./src/hlir16/
git apply find_system_p4test.patch

%build

%install

rm -rf %{buildroot}

mkdir -p %{buildroot}%{t4p4sroot}
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_unitdir}

install -m 755 packaging/setup_eth_wlan_bridge.sh %{buildroot}%{t4p4sroot}
install -m 755 packaging/%{shortname}-start %{buildroot}%{_bindir}
install -m 755 packaging/%{shortname}-p4rtshell %{buildroot}%{_bindir}
install -m 644 packaging/%{shortname}.service %{buildroot}%{_unitdir}
cp -r ./* %{buildroot}%{t4p4sroot}


%post
python3 -m pip install -r %{t4p4sroot}/requirements.txt
%systemd_post %{shortname}.service

git clone -b v1.37.0 --recursive --shallow-submodules --depth=1 https://github.com/grpc/grpc %{grpcroot}

mkdir %{piroot} && cd %{piroot}
git init
git remote add origin https://github.com/p4lang/PI
git fetch --depth 1 origin a5fd855d4b3293e23816ef6154e83dc6621aed6a
git checkout FETCH_HEAD
git submodule update --init --recursive --depth=1

git clone --depth=1 https://github.com/P4ELTE/P4Runtime_GRPCPP %{p4rtroot}

cd %{p4rtroot}
./install.sh
./compile.sh

%preun
%systemd_preun %{shortname}.service

%postun
%systemd_postun %{shortname}.service

%files
%{_bindir}/*
%{_unitdir}/%{shortname}.service
%{t4p4sroot}/examples/*
%{t4p4sroot}/src/*
%{t4p4sroot}/*
%{grpcroot}/*
%{piroot}/*
%{p4rtroot}/*

%dir %{t4p4sroot}/examples
