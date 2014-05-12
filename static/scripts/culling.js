function validateForm(form)
{
    var invalidChains = false;
    var textInChainsBox = form.pastedInfo.value.trim();
    if (textInChainsBox.length === 0 || ((textInChainsBox.match(/\n/g) || []).length === 0))
    {
        // The input is invalid if no text is present in the chain input text box, or if there is not at least one new line character
		// (as this ensures a minimum of two chains).
        var invalidChains = true;
        document.getElementById('noInputsWarning').style.background = '#F7730E';
        document.getElementById('noInputsWarning').style.display = 'inherit';
    }
    else
    {
        document.getElementById('noInputsWarning').style.background = 'inherit';
        document.getElementById('noInputsWarning').style.display = 'none';
    }
    var invalidSeqIden = invalidNumber(form.pc, document.getElementById('SeqIdenInfo'), 5, 100);
    var invalidRes = invalidResolutionCheck(form.minRes, document.getElementById('minResInfo'), form.maxRes, document.getElementById('maxResInfo'), 0, 100)
    var invalidRVal = invalidNumber(form.maxRVal, document.getElementById('RValInfo'), 0, 1);
    var invalidLength = invalidLengthCheck(form.minLen, form.enforceMinLengthYes.checked, document.getElementById('minLengthInfo'),
                                           form.maxLen, form.enforceMaxLengthYes.checked, document.getElementById('maxLengthInfo'),
                                           0);
	var emailAddress = form.email.value.trim();
	var invalidEmail = (emailAddress.length === 0);  // Invalid if there is no text.
	invalidEmail = invalidEmail || ((emailAddress.match(/@/g) || []).length !== 1);  // Invalid if there is not exactly one @ (the || [] prevents returning null when there is no @).
	if (invalidEmail)
	{
		// There was no email address supplied.
		document.getElementById('emailInfo').style.background = '#F7730E';
    }
    else
    {
		document.getElementById('emailInfo').style.background = 'inherit';
	}

    if (invalidChains || invalidSeqIden || invalidRes || invalidRVal || invalidLength || invalidEmail)
    {
        alert('WARNING Some parameters have invalid values. The fields with invalid values are highlighted in orange. Please correct the highlighted fields before submitting.');
        if (invalidChains)
        {
            // If the chains input is invalid, then scroll to the top.
            window.scrollTo(0,0);
        }
        return false;
    }
	else
	{
		// Check that chains are all valid chains.
		var invalidChainID = false;
		var individualChains = textInChainsBox.split('\n');
		for (var i = 0; i < individualChains.length; i++)
		{
			var potentialChain = individualChains[i].trim();
			if (! potentialChain.match(/^[0-9][A-Za-z0-9]{4}/g))
			{
				// A chain must start with a number, and then be a string of 4 numbers or characters.
				alert('Chain ' + potentialChain + ' is not a valid chain identifier.');
				window.scrollTo(0,0);
				return false;
			}
		}
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