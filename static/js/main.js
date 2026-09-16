// حذف شخص
async function deletePerson(personId) {
    if (!confirm('هل أنت متأكد من حذف هذا الشخص؟')) return;

    try {
        const response = await fetch(`/api/persons/${personId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        if (data.success) {
            window.location.reload();
        }
    } catch (error) {
        alert('❌ حدث خطأ في الحذف');
    }
}
