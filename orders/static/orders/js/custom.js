document.addEventListener('DOMContentLoaded', function() {
    // Configuration when website loads

    // Set up the Sidenav elements
    const nav_elems = document.querySelectorAll('.sidenav');
    const nav_options = {
        inDuration: 350,
        outDuration: 350,
        edge: 'left'
    };
    const nav_instances = M.Sidenav.init(nav_elems, nav_options);

});