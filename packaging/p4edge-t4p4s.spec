%{!?t4p4sroot: %global t4p4sroot /root/t4p4s}
%{!?shortname: %global shortname t4p4s}

Name:           p4edge-t4p4s
Version:        0.0.0
Release:        0%{?dist}
Summary:        P4Edge t4p4s
License:        Apache 2.0
URL:            https://github.com/p4edge/t4p4s
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3, python3-pip, python3-venv, ccache, lsof, netcat
Requires:       ninja-build, libdpdk-dev
BuildRequires:  debbuild-macros-systemd, git
BuildRequires:  protobuf-compiler, protobuf-compiler-grpc, libprotobuf-dev
BuildRequires:  pkg-config, libgrpc-dev, libgrpc++-dev, libboost-thread-dev
Packager:       Dávid Kis <kidraai@.inf.elte.hu>

%description
P4Edge t4p4s

%prep
%autosetup
git apply --directory=src/hlir16 ./packaging/find_system_p4test.patch
git apply --directory=third_party/P4Runtime_GRPCPP ./packaging/change_t4p4s_dir.patch

%build
cd third_party/P4Runtime_GRPCPP
./install.sh
T4P4SDIR="../.." ./compile.sh
cd ../../

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
mkdir -p %{buildroot}%{t4p4sroot}/examples

%post
%systemd_post %{shortname}.service
python3 -m venv %{t4p4sroot}/.venv
%{t4p4sroot}/.venv/bin/python -m pip install -r %{t4p4sroot}/requirements.txt

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

%dir %{t4p4sroot}/examples
