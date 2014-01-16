function validateForm(form)
{
    var invalidSeqIden = invalidNumber(form.pc, document.getElementById('SeqIdenInfo'), 5, 100);
    var invalidRes = invalidResolutionCheck(form.minRes, document.getElementById('minResInfo'), form.maxRes, document.getElementById('maxResInfo'), 0, 100)
    var invalidRVal = invalidNumber(form.maxRVal, document.getElementById('RValInfo'), 0, 1);
    var invalidLength = invalidLengthCheck(form.minLen, form.enforceMinLengthYes.checked, document.getElementById('minLengthInfo'),
                                           form.maxLen, form.enforceMaxLengthYes.checked, document.getElementById('maxLengthInfo'),
                                           0);
    var invalidIntraEntrySeqIden = false;
    if (form.cullByEntryYes.checked && form.intraEntryCullYes.checked)
    {
        var invalidIntraEntrySeqIden = invalidNumber(form.intraEntryPC, document.getElementById('intraEntryInfo'), 5, 100);
    }
    else
    {
        document.getElementById('intraEntryInfo').style.background = 'inherit';
    }
    if (invalidSeqIden || invalidRes || invalidRVal || invalidLength || invalidIntraEntrySeqIden)
    {
        alert("WARNING Some parameters have invalid values. The fields with invalid values are highlighted in orange. Please correct the highlighted fields before submitting.");
        return false;
    }
    return true;
}

function invalidLengthCheck(minLenObj, minLenEnforced, minLenWarningObj, maxLenObj, maxLenghEnforced, maxLenWarningObj, lowerBound)
{
    var minLenValue = +(minLenObj.value);//parseFloat(minLenObj.value);
    var maxLenValue = +(maxLenObj.value);//parseFloat(maxLenObj.value);
    var minLenInvalid = false;
    var maxLenInvalid = false;

    if (minLenEnforced && (isNaN(minLenValue) || minLenValue < lowerBound))
    {
        minLenInvalid = true;
    }
    if (maxLenghEnforced && (isNaN(maxLenValue) || maxLenValue < lowerBound))
    {
        maxLenInvalid = true;
    }
    if (minLenEnforced && maxLenghEnforced && !isNaN(minLenValue) && !isNaN(maxLenValue) && minLenValue >= maxLenValue)
    {
        minLenInvalid = true;
        maxLenInvalid = true;
    }

    if (minLenInvalid)
    {
        minLenWarningObj.style.background = '#F7730E';
    }
    else
    {
        minLenWarningObj.style.background = 'inherit';
    }
    if (maxLenInvalid)
    {
        maxLenWarningObj.style.background = '#F7730E';
    }
    else
    {
        maxLenWarningObj.style.background = 'inherit';
    }

    return minLenInvalid || maxLenInvalid;
}

function invalidNumber(obj, warningObj, lowerBound, upperBound)
{
    var objValue = +(obj.value);//parseFloat(obj.value);
    if (isNaN(objValue) || objValue < lowerBound || objValue > upperBound)
    {
        // If the objects value is not a number, or the number is either below or above the permissible values.
        warningObj.style.background = '#F7730E';
        return true;
    }
    else
    {
        // The value is valid.
        warningObj.style.background = 'inherit';
        return false;
    }
}

function invalidResolutionCheck(minResObj, minResWarningObj, maxResObj, maxResWarningObj, lowerBound, upperBound)
{
    var minResValue = +(minResObj.value);//parseFloat(minResObj.value);
    var maxResValue = +(maxResObj.value);//parseFloat(maxResObj.value);
    var minResInvalid = false;
    var maxResInvalid = false;

    if (isNaN(minResValue) || minResValue < lowerBound || minResValue > upperBound || (!isNaN(maxResValue) && minResValue >= maxResValue))
    {
        minResInvalid = true;
        minResWarningObj.style.background = '#F7730E';
    }
    else
    {
        minResWarningObj.style.background = 'inherit';
    }

    if (isNaN(maxResValue) || maxResValue < lowerBound || maxResValue > upperBound || (!isNaN(minResValue) && minResValue >= maxResValue))
    {
        maxResInvalid = true;
        maxResWarningObj.style.background = '#F7730E';
    }
    else
    {
        maxResWarningObj.style.background = 'inherit';
    }

    return minResInvalid || maxResInvalid;
}

function hideElement(obj)
{
    obj.style.visibility = 'hidden';
}

function showElement(obj)
{

    obj.style.visibility = 'visible';
}

function disableElement(obj)
{
    obj.disabled = true;
    obj.style.background = '#222222';
}

function enableElement(obj)
{
    obj.disabled = false;
    obj.style.background = '#FFFFFF';
}