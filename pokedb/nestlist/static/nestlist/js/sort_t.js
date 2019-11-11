function sortTable(tableId, n) {
var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;

table = document.getElementById(tableId);
switching = true;
dir = "asc";
while (switching) {
    switching = false;
    rows = table.getElementsByTagName("tr");
    headers = table.getElementsByTagName("th");
    for (i = 0; i < headers.length; i++) {
        h = headers[i]
        h.classList.remove("sort-asc");
        h.classList.remove("sort-desc");
        h.classList.remove("current-sort");
    }
    headers[n].classList.add("current-sort");
    if (rows.length < 3) {
        break;
    }
    if (dir == "asc") {
        headers[n].classList.add("sort-asc")
    } else {
        headers[n].classList.add("sort-desc")
    }
    for (i = 1; i < (rows.length - 1); i++) {
        shouldSwitch = false;
        x = rows[i].getElementsByTagName("td")[n];
        y = rows[i + 1].getElementsByTagName("td")[n];
        var cmpX=isNaN(parseInt(x.innerHTML))?x.innerHTML.toLowerCase():parseInt(x.innerHTML);
        var cmpY=isNaN(parseInt(y.innerHTML))?y.innerHTML.toLowerCase():parseInt(y.innerHTML);
        cmpX=(cmpX=='-')?0:cmpX;
        cmpY=(cmpY=='-')?0:cmpY;
        var Xint = isNaN(cmpX)
        var Yint = isNaN(cmpY)
        if (!Xint && Yint) {
            shouldSwitch= true;
            break;
        }
        if (dir == "asc") {
            if (cmpX > cmpY) {
                shouldSwitch= true;
                break;
            }
        } else if (dir == "desc") {
            if (cmpX < cmpY) {
                shouldSwitch= true;
                break;
            }
        }
    }
    if (shouldSwitch) {
        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
        switching = true;
        switchcount ++;
    } else {
        if (switchcount == 0 && dir == "asc") {
            dir = "desc";
            switching = true;
        }
    }
}
}