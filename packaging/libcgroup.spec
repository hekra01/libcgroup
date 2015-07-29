%global soversion_major 1
%global soversion 1.0.41
%global _hardened_build 1

Summary: Library to control and monitor control groups
Name: libcgroup
Version: 0.41
Release: 8%{?dist}
License: LGPLv2+
Group: Development/Libraries
URL: http://libcg.sourceforge.net/
Source0: %{name}-%{version}.tar.bz2
Source1: cgconfig.service
Source2: cgred.service
Source3: cgred.sysconfig

BuildRequires: byacc, coreutils, flex, pam-devel, systemd
#Requires(pre): shadow-utils
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
Control groups infrastructure. The library helps manipulate, control,
administrate and monitor control groups and the associated controllers.

%package tools
Summary: Command-line utility programs, services and daemons for libcgroup
Group: System Environment/Base
Requires: %{name}%{?_isa} = %{version}-%{release}

%description tools
This package contains command-line programs, services and a daemon for
manipulating control groups using the libcgroup library.

%package pam
Summary: A Pluggable Authentication Module for libcgroup
Group: System Environment/Base
Requires: %{name}%{?_isa} = %{version}-%{release}

%description pam
Linux-PAM module, which allows administrators to classify the user's login
processes to pre-configured control group.

%package devel
Summary: Development libraries to develop applications that utilize control groups
Group: Development/Libraries
Requires: %{name}%{?_isa} = %{version}-%{release}

%description devel
It provides API to create/delete and modify cgroup nodes. It will also in the
future allow creation of persistent configuration for control groups and
provide scripts to manage that configuration.

%prep
%setup  -q  -n %{name}-%{version}

%build
%configure --enable-pam-module-dir=%{_libdir}/security \
           --enable-opaque-hierarchy="name=systemd"
#           --disable-daemon
make %{?_smp_mflags}

%install
make DESTDIR=$RPM_BUILD_ROOT install

# install config files
install -d ${RPM_BUILD_ROOT}%{_sysconfdir}
install -m 644 samples/cgconfig.conf $RPM_BUILD_ROOT/%{_sysconfdir}/cgconfig.conf
install -d $RPM_BUILD_ROOT/%{_sysconfdir}/cgconfig.d
install -m 644 samples/cgrules.conf $RPM_BUILD_ROOT/%{_sysconfdir}/cgrules.conf
install -m 644 samples/cgsnapshot_blacklist.conf $RPM_BUILD_ROOT/%{_sysconfdir}/cgsnapshot_blacklist.conf

# sanitize pam module, we need only pam_cgroup.so
mv -f $RPM_BUILD_ROOT%{_libdir}/security/pam_cgroup.so.*.*.* $RPM_BUILD_ROOT%{_libdir}/security/pam_cgroup.so
rm -f $RPM_BUILD_ROOT%{_libdir}/security/pam_cgroup.la $RPM_BUILD_ROOT/%{_libdir}/security/pam_cgroup.so.*

rm -f $RPM_BUILD_ROOT/%{_libdir}/*.la

# install unit and sysconfig files
install -d ${RPM_BUILD_ROOT}%{_unitdir}
install -m 644 %SOURCE1 ${RPM_BUILD_ROOT}%{_unitdir}/
install -m 644 %SOURCE2 ${RPM_BUILD_ROOT}%{_unitdir}/
install -d ${RPM_BUILD_ROOT}%{_sysconfdir}/sysconfig
install -m 644 %SOURCE3 ${RPM_BUILD_ROOT}%{_sysconfdir}/sysconfig/cgred

%pre
getent group cgred >/dev/null || groupadd -r cgred

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%pre tools
getent group cgred >/dev/null || groupadd -r cgred

%post tools
if [ $1 -eq 1 ] ; then 
    # Initial installation 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi
%systemd_post cgconfig.service cgred.service

%preun tools
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable cgconfig.service > /dev/null 2>&1 || :
    /bin/systemctl stop cgconfig.service > /dev/null 2>&1 || :
    /bin/systemctl --no-reload disable cgred.service > /dev/null 2>&1 || :
    /bin/systemctl stop cgred.service > /dev/null 2>&1 || :
fi
%systemd_preun cgconfig.service cgred.service

%postun tools
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart cgconfig.service >/dev/null 2>&1 || :
    /bin/systemctl try-restart cgred.service >/dev/null 2>&1 || :
fi
%systemd_postun_with_restart cgconfig.service cgred.service

%triggerun -- libcgroup < 0.38
# Save the current service runlevel info
# User must manually run systemd-sysv-convert --apply cgconfig/cgred
# to migrate them to systemd targets
/usr/bin/systemd-sysv-convert --save cgconfig >/dev/null 2>&1 ||:
/usr/bin/systemd-sysv-convert --save cgred >/dev/null 2>&1 ||:

# Run these because the SysV package being removed won't do them
/sbin/chkconfig --del cgconfig >/dev/null 2>&1 || :
/bin/systemctl try-restart cgconfig.service >/dev/null 2>&1 || :
/sbin/chkconfig --del cgred >/dev/null 2>&1 || :
/bin/systemctl try-restart cgred.service >/dev/null 2>&1 || :

%files
%doc COPYING README
%{_libdir}/libcgroup.so.*

%files tools
%doc COPYING README README_systemd
%config(noreplace) %{_sysconfdir}/cgconfig.conf
%config(noreplace) %{_sysconfdir}/cgconfig.d
%config(noreplace) %{_sysconfdir}/cgrules.conf
%config(noreplace) %{_sysconfdir}/cgsnapshot_blacklist.conf
%config(noreplace) %{_sysconfdir}/sysconfig/cgred
/usr/bin/cgcreate
/usr/bin/cgget
/usr/bin/cgset
/usr/bin/cgdelete
/usr/bin/lscgroup
/usr/bin/lssubsys
/usr/sbin/cgconfigparser
/usr/sbin/cgrulesengd
/usr/sbin/cgclear
/usr/bin/cgsnapshot
%attr(2755, root, cgred) /usr/bin/cgexec
%attr(2755, root, cgred) /usr/bin/cgclassify
%attr(0644, root, root) %{_mandir}/man1/*
%attr(0644, root, root) %{_mandir}/man5/*
%attr(0644, root, root) %{_mandir}/man8/*
%{_unitdir}/cgconfig.service
%{_unitdir}/cgred.service

%files pam
%doc COPYING README
%attr(0755,root,root) %{_libdir}/security/pam_cgroup.so

%files devel
%doc COPYING README
%{_includedir}/libcgroup.h
%{_includedir}/libcgroup/*.h
%{_libdir}/libcgroup.so
%{_libdir}/pkgconfig/libcgroup.pc

